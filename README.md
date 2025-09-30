# TruthLoop

**TruthLoop** is an AI-powered meme-to-video generator that transforms user-uploaded images of text into short, humorous videos. With just a few clicks, users can turn text memes into fully narrated videos and share them directly to TikTok—making meme creation and social sharing effortless.

---

## Features

* **Text-to-Video Generation:** Upload images of text, and AI automatically generates a short, funny video.
* **AI Script & Narration:** Intelligent scriptwriting and voice narration based on the text content.
* **Seamless Video Assembly:** Automatic editing, timing, and visual effects to create engaging clips.
* **Direct TikTok Sharing:** Post videos instantly from the app with one click.
* **Minimalist Frontend:** Simple and intuitive interface—just upload and preview.
* **Robust Python Backend:** Handles AI processing, video creation, and social media integration.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/TruthLoop.git
cd TruthLoop
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Redis (Required for Caching & Background Tasks)

```bash
sudo apt-get install redis-server
sudo systemctl enable redis-server.service
sudo systemctl start redis-server.service
```

---

## Running the App

Start the Streamlit frontend:

```bash
streamlit run app.py
```

The app should now be accessible at `http://localhost:8501`.

---

## Usage

1. Upload an image containing text or a meme.
2. Preview the AI-generated video in the built-in player.
3. Share the video directly to TikTok with one click.

---

## Environment variables
Create a `.env` file in the root directory and add the following variables:

```env
OPENAI_API_KEY="your_openai_api_key"
REDIS_HOST="your_redis_host"
REDIS_PORT="your_redis_port"
REDIS_PASSWORD="your_redis_password"
```
---

## Project Structure

```
TruthLoop/
├── app.py               # Main Streamlit app
├── agents/              # AI agents for narration, script, and video generation
├── requirements.txt     # Python dependencies
├── README.md
└── ...
```

---
## Website Link
https://truthloop-cbwyn6axbt6dnnva2rwzjw.streamlit.app/

## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m "Add feature"`)
4. Push to the branch (`git push origin feature-name`)
5. Open a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


