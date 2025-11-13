import React, {useState, useRef, useEffect} from 'react';

function Bubble({message, from}){
  const isUser = from==='user';
  return (
    <div style={{display:'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', margin:'8px 0'}}>
      <div style={{
        maxWidth: '75%',
        background: isUser ? '#0b63d6' : '#f1f1f1',
        color: isUser ? 'white' : '#111',
        padding: '10px 14px',
        borderRadius: 14,
        borderTopRightRadius: isUser ? 2 : 14,
        borderTopLeftRadius: isUser ? 14 : 2,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        whiteSpace: 'pre-wrap'
      }}>
        {message}
      </div>
    </div>
  );
}

export default function App(){
  const [messages, setMessages] = useState([
    {from:'agent', text:'Hi — I can help schedule appointments. Say "I need to book" to start.'}
  ]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const boxRef = useRef(null);

  useEffect(()=>{
    if(boxRef.current){
      boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }
  }, [messages]);

  async function send(){
    if(!text.trim()) return;
    const userMsg = text.trim();
    setMessages(m=>[...m, {from:'user', text:userMsg}]);
    setText('');
    setLoading(true);
    try{
      const res = await fetch('/api/chat/message', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user_id:'local', message: userMsg})
      });
      const data = await res.json();
      setMessages(m=>[...m, {from:'agent', text: data.response}]);
    }catch(err){
      setMessages(m=>[...m, {from:'agent', text: 'Error: could not reach backend.'}]);
    }finally{
      setLoading(false);
    }
  }

  function onKey(e){
    if(e.key==='Enter' && !e.shiftKey){
      e.preventDefault();
      send();
    }
  }

  return (
    <div style={{height:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'#f6f7fb'}}>
      <div style={{width:'100%', maxWidth:900, height:'80vh', background:'white', borderRadius:12, boxShadow:'0 6px 30px rgba(12,20,40,0.08)', display:'flex', flexDirection:'column', overflow:'hidden'}}>
        <div style={{padding:16, borderBottom:'1px solid #eee', fontWeight:700}}>Appointment Agent</div>
        <div ref={boxRef} style={{flex:1, padding:16, overflowY:'auto'}}>
          {messages.map((m,i)=>(<Bubble key={i} message={m.text} from={m.from}/>))}
        </div>
        <div style={{padding:12, borderTop:'1px solid #eee', display:'flex', gap:8}}>
          <textarea value={text} onChange={e=>setText(e.target.value)} onKeyDown={onKey} placeholder='Type a message (e.g. "I need to book")' style={{flex:1, resize:'none', padding:10, borderRadius:8, border:'1px solid #ddd'}} rows={2}></textarea>
          <div style={{display:'flex', flexDirection:'column', gap:8}}>
            <button onClick={send} disabled={loading} style={{padding:'10px 14px', borderRadius:8, background:'#0b63d6', color:'white', border:'none'}}> {loading ? 'Sending...' : 'Send'} </button>
            <button onClick={()=>{setMessages([{from:'agent', text:'Hi — I can help schedule appointments. Say "I need to book" to start.'}]); setText('');}} style={{padding:'8px 10px', borderRadius:8, background:'#f1f1f1', border:'none'}}>Reset</button>
          </div>
        </div>
      </div>
    </div>
  );
}
