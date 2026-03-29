import './ChatMessage.css'

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <div className="avatar">🏛️</div>}
      <div className="bubble-wrap">
        <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
          {message.text}
        </div>
        <span className="timestamp">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  )
}
