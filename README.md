# 🎙️ OmniVoice Studio — Google Colab Setup

গুগল কোলাবে (Google Colab) সরাসরি **OmniVoice Studio** রান করার জন্য নিচের বোতামটিতে ক্লিক করুন:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shakib30/OmniVoice-Studio-google-colab/blob/main/omnivoice_colab.ipynb)

---

## ⚡ মূল বৈশিষ্ট্যসমূহ (Key Features)

* **ডাইনামিক ভাষা সাপোর্ট (Dynamic Language Support):** বাংলা, ইংরেজি, হিন্দি, উর্দু, তুর্কি, স্প্যানিশসহ আরও অনেক ভাষা সাপোর্ট করে।
* **১৬+ এআই প্রোভাইডার (16+ AI Providers):** Groq, OpenRouter, Google, Mistral, OpenAI, Ollama, Cerebras, SambaNova সহ জনপ্রিয় সব এআই প্রোভাইডার সাপোর্ট করে।
* **ডাইনামিক পোর্ট ফরওয়ার্ডিং (Dynamic Port Forwarding):** Cloudflare Free/API, Ngrok, SSH, Localhost টানেলের মাধ্যমে সহজেই লোকাল বা কোলাব পোর্ট ফরওয়ার্ডিং সুবিধা।
* **অটোমেটেড স্পিকার ডিটেকশন (Automated Speaker Detection):** Pyannote Audio এবং WhisperX এর মাধ্যমে স্বয়ংক্রিয় স্পিকার ডায়রিয়াইজেশন সেটআপ।
* **জিপিইউ রানটাইম সামঞ্জস্যতা (GPU Runtime Compatibility):** Google Colab T4 GPU রানটাইমের জন্য সম্পূর্ণ অপ্টিমাইজড।

---

## 🔑 গুগল কোলাব সিক্রেটস সেটআপ (Google Colab Secrets Setup)

কোলাব নোটবুকটি ভালোভাবে চালানোর জন্য নিচের সিক্রেট কি-গুলো আপনার গুগল কোলাবের বাম পাশের মেনু থেকে **Secrets (Key Icon)**-এ যুক্ত করে নিন এবং **Notebook access** অন করে দিন:

1. `HF_TOKEN`: Hugging Face Token (Pyannote স্পিকার সনাক্তকরণের জন্য আবশ্যক)।
2. `NGROK_AUTH_TOKEN`: Ngrok টানেল ব্যবহার করতে চাইলে এটি প্রয়োজন।
3. `CLOUDFLARE_TUNNEL_TOKEN`: Cloudflare কাস্টম ডোমেইন টানেল ব্যবহার করতে চাইলে এটি প্রয়োজন।

---

## 🚀 How to Run / কীভাবে রান করবেন

1. উপরের **Open In Colab** বাটনে ক্লিক করুন।
2. গুগল কোলাব পেজ ওপেন হলে রানটাইম টাইপ **T4 GPU** নিশ্চিত করুন।
3. সব সেল পর্যায়ক্রমে রান (Run) করুন।
