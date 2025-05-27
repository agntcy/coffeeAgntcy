import React from 'react';
import Graph from './components/MainArea/Graph';
import Chat from './components/Chat/Chat';
import Footer from './components/MainArea/Footer';
import './App.css';

const App = () => {
  return (
    <div className="app-container">
      <div className="sidebar">
        <Chat />
      </div>
      <div className="main-area">
        <header className="header">Corto</header>
        <div className="main-panel">
          <Graph />
        </div>
        <Footer />
      </div>
    </div>
  );
};

export default App;
