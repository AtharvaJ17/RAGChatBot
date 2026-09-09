import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'
import ChatComponent from './components/ChatComponent.jsx'


function App() {
  return (
    <div className="app-wrapper">
      <div className="chat-container">
        <ChatComponent />
      </div>
    </div>
  );
}

export default App
