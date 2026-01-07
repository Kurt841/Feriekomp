import React from 'react';

const Footer = () => (
  <footer className="w-full py-5 px-8 text-center text-gray-400 text-sm bg-gray-950 shadow-inner border-t border-gray-800">
    &copy; {new Date().getFullYear()} Feriekompensasjon kalkulator. Alle rettigheter reservert.
  </footer>
);

export default Footer; 