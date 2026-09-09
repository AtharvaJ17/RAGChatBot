## Known Limitation

Transcript retrieval works fine locally, but YouTube blocks these requests when they come from datacenter IPs — which includes most cloud hosts and free-tier proxies — so this cloud deployment can get rate-limited. I integrated proxy-based IP rotation to route around Render's own IP, which is the correct fix in principle — full reliability in production requires residential proxies rather than a free datacenter tier, since YouTube blocks both alike.
