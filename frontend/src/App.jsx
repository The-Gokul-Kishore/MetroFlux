import { useState, useEffect } from 'react'
import axios from 'axios'
import Plot from 'react-plotly.js';

import './App.css'
function App(){
  const [query,setQuery]= useState('')
  const [messages,setMessages]= useState([])
  const [loading,setLoading]= useState(false)
    useEffect(() => {
    window.dispatchEvent(new Event('resize'))
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    const usermessage = {role: 'user', content: query}
    setMessages((prev) => [...prev, usermessage])
    try{
      const res = await axios.post('http://127.0.0.1:8000/query', {query: query})
    
    const botMessage = {
      role: 'bot',
      content: res.data.output_text,
  graph: res.data.graph_json ? JSON.parse(res.data.graph_json) : null,
    };
    console.log(botMessage)
      setMessages((prev)=>[...prev,botMessage])
      setQuery('')
  } catch (err) {
      console.error(err)
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: 'Error calling API: ' + err.message },
      ])
    }

}  
return (
    <div className="chat-container">
      <h2>🌦️ MetroFlux Weather Agent</h2>
      <div className="chat-box">
        {messages.map((msg,idx)=>(
    <div key={idx} className={`message ${msg.role}`}>
      <strong>{msg.role === 'user' ? 'You' : 'Agent'}:</strong>{' '}
      {msg.content}

      {msg.role === 'bot' && msg.graph && (
          <div className="graph-container">

        <Plot
          data={msg.graph.data}
          layout={msg.graph.layout}
          config={{ responsive: true }}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
      )}
    </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="input-area">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask something about the weather..."
        />
        <button type="submit">Send</button>
      </form>

    </div>
  )
}

export default App

