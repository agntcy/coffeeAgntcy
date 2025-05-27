import React from 'react';
import './Footer.css';  // import the CSS file

function Footer() {
  return (
    <footer className="footer">
      <div>©2025 Cisco Systems, Inc. All rights reserved.</div> 
      <div className='footer_links'>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="/contact">Contact</a>
      </div>
    </footer>
  );
}

export default Footer;
