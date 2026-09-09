import { useState } from "react";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const useChatbot = () => {
  const [messages, setMessages] = useState([
    { text: "Paste a YouTube video ID to get started.", sender: "bot" },
  ]);
  const [videoSet, setVideoSet] = useState(false);

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const sendMessage = async (message) => {
    await delay(500);
    const newMessages = [...messages, { text: message, sender: "user" }];
    setMessages(newMessages);

    try {
      if (!videoSet) {
        const response = await axios.post(`${API_BASE_URL}/api/set-video/`, {
          video_id: message.trim(),
        });

        const botMessage = response.data.reply || response.data.error;
        setMessages([...newMessages, { text: botMessage, sender: "bot" }]);

        if (response.data.reply) {
          setVideoSet(true);
        }
      } else {
        const response = await axios.post(`${API_BASE_URL}/api/chat/`, {
          message,
        });

        const botMessage = response.data.reply;
        setMessages([...newMessages, { text: botMessage, sender: "bot" }]);
      }
    } catch (error) {
      console.error("Error fetching AI response:", error);
      setMessages([
        ...newMessages,
        { text: "Something went wrong. Please try again.", sender: "bot" },
      ]);
    }
  };

  return { messages, sendMessage, videoSet };
};

export default useChatbot;