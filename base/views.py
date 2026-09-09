import json
import traceback

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import (
    HuggingFaceEndpoint,
    ChatHuggingFace,
    HuggingFaceEndpointEmbeddings,
)
from langchain_community.vectorstores import FAISS

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser


rag_state = {
    "video_id": None,
    "main_chain": None,
}


prompt = PromptTemplate(
    template="""
      You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
    input_variables=["context", "question"],
)


def format_docs(retrieved_docs):
    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return context_text


def get_llm():
    endpoint = HuggingFaceEndpoint(
        repo_id="deepseek-ai/DeepSeek-V3-0324",
        task="text-generation",
        max_new_tokens=512,
        temperature=0.2,
        provider="auto",
        huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
    )
    return ChatHuggingFace(llm=endpoint)


def get_embeddings():
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-mpnet-base-v2",
        task="feature-extraction",
        huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
    )


@csrf_exempt
@require_POST
def set_video(request):
    try:
        body = json.loads(request.body)
        video_id = body.get("video_id", "").strip()

        if not video_id:
            return JsonResponse({"error": "video_id is required"}, status=400)

        try:
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id, languages=["en"])
            transcript = " ".join(
                snippet.text for snippet in fetched_transcript
            )
            print("Step 1a done, transcript length:", len(transcript))

        except TranscriptsDisabled:
            return JsonResponse(
                {"error": "No captions available for this video."},
                status=400,
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = splitter.create_documents([transcript])
        print("Step 1b done, chunk count:", len(chunks))

        embeddings = get_embeddings()
        print("Embeddings object created")

        vector_store = FAISS.from_documents(chunks, embeddings)
        print("Vector store built")

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )

        print("Retriever created")

        llm = get_llm()
        print("LLM object created")

        parser = StrOutputParser()

        parallel_chain = RunnableParallel(
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
        )

        main_chain = parallel_chain | prompt | llm | parser

        print("Chain assembled")

        rag_state["video_id"] = video_id
        rag_state["main_chain"] = main_chain

        return JsonResponse(
            {
                "reply": f"Video '{video_id}' indexed. Ask me anything about it!"
            }
        )

    except Exception as e:
        print("ERROR in set_video:")
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def rag_chat(request):
    try:
        body = json.loads(request.body)
        message = body.get("message", "")

        if rag_state["main_chain"] is None:
            return JsonResponse(
                {"reply": "Please set a video ID first."},
                status=400,
            )

        answer = rag_state["main_chain"].invoke(message)

        return JsonResponse({"reply": answer})

    except Exception as e:
        print("ERROR in rag_chat:")
        traceback.print_exc()
        return JsonResponse(
            {"reply": f"Error: {str(e)}"},
            status=500,
        )