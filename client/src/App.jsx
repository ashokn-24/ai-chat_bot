import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
  TypingIndicator,
  ConversationList,
  Conversation,
} from "@chatscope/chat-ui-kit-react";
import { useEffect, useState } from "react";
import axios from "axios";

const App = () => {
  const [typing, setTyping] = useState(false);
  const [messages, setMessages] = useState([
    {
      message: "Hii, How can i help you",
      sender: "Bot",
      direction: "incoming",
    },
  ]);

  const [historys, setHistory] = useState([]);

  useEffect(() => {
    const fetchChat = async () => {
      const res = await axios.get("http://127.0.0.1:8000/chats");
      setHistory(res.data);
    };
    fetchChat();
  }, []);

  const handleSend = async (message) => {
    if (!message.trim()) return; // Prevent empty messages

    setMessages((prevMessages) => [
      ...prevMessages,
      {
        message,
        sender: "User",
        direction: "outgoing",
      },
    ]);

    setTyping(true);

    await processResponse(message);
  };

  const processResponse = async (userMessage) => {
    const payload = { user_message: userMessage };

    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", payload);

      const botReply = response.data.bot_reply;

      console.log("Bot Reply:", botReply);

      setMessages((prevMessages) => [
        ...prevMessages,

        {
          message: botReply,
          sender: "Bot",
          direction: "incoming",
        },
      ]);
    } catch (error) {
      console.error("API Error:", error);

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: userMessage,
          sender: "User",
          direction: "outgoing",
        },
        {
          message: "Error connecting to the chatbot service.",
          sender: "Bot",
          direction: "incoming",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  const handleClickChat = async (id) => {
    const res = await axios.get(`http://127.0.0.1:8000/chat/${id}`);

    console.log("data", res.data);
    setMessages([
      {
        message: res.data.user_message,
        sender: "User",
        direction: "outgoing",
      },
      {
        message: res.data.bot_reply,
        sender: "Bot",
        direction: "incoming",
      },
    ]);
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-200">
      <div className="relative h-full w-full rounded-lg shadow-lg bg-white">
        <MainContainer>
          <ConversationList className="">
            <div className="py-2">
              <h3 className="text-center font-bold text-lg">HISTORY</h3>
            </div>
            {historys &&
              historys.map((chat, i) => {
                return (
                  <Conversation
                    key={i}
                    info={chat.bot_reply}
                    lastSenderName="Bot"
                    name={chat.user_message}
                    onClick={() => handleClickChat(chat.id)}
                  />
                );
              })}
          </ConversationList>
          <ChatContainer>
            <MessageList
              typingIndicator={
                typing ? <TypingIndicator content={"Bot is typing"} /> : null
              }
            >
              {messages &&
                messages?.map((message, i) => (
                  <Message
                    key={i}
                    model={{
                      message: message.message,
                      direction: message.direction,
                      sender: message.sender,
                    }}
                  />
                ))}
            </MessageList>
            <MessageInput
              autoFocus
              attachButton={false}
              placeholder="Type a message..."
              onSend={handleSend}
            />
          </ChatContainer>
        </MainContainer>
      </div>
    </div>
  );
};

export default App;
