import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sanket (संकेत) – Sign to Speech | Indian Sign Language Translator",
  description: "Real-time AI bridge translating Indian Sign Language (ISL) gestures into text and speech across Indian languages with on-device privacy.",
  manifest: "/manifest.json",
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="icon" type="image/svg+xml" href="/icon.svg" />
      </head>
      <body className="min-h-screen bg-space-950 text-slate-100 antialiased selection:bg-gold-500 selection:text-space-950">
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // PWA Service Worker Registration
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').then(
                    function(reg) {
                      console.log('Sanket PWA registered: ', reg.scope);
                    },
                    function(err) {
                      console.log('Sanket PWA registration warning: ', err);
                    }
                  );
                });
              }

              // Sanket Dynamic Tab Favicon Pulsing when Hidden
              (function(){
                var NV="#152340",CY="#22d3ee",OR="#f58220";
                var F=[[[30,74],[22,62],[17,51],[14,41]],[[34,58],[32,44],[31,34],[30,25]],[[44,56],[44,41],[44,30],[44,20]],[[54,58],[56,44],[57,35],[58,27]],[[63,64],[67,54],[69,47],[71,40]]];
                var PALM="M45 88L30 74L34 58L44 56L54 58L63 64Z";
                var ARCS=[[16,12.6,9.85],[28,22.1,17.2],[40,31.5,24.6]];
                function path(f){return "M"+f.map(function(p){return p.join(" ")}).join("L")}
                function mark(n){
                  var sw=7,r=6,s="";
                  var lines=[PALM].concat(F.map(path));
                  lines.forEach(function(d){ s+='<path d="'+d+'" fill="none" stroke="'+CY+'" stroke-width="'+sw+'" stroke-linecap="round" stroke-linejoin="round"/>'; });
                  var pts=[[45,88]];
                  F.forEach(function(f){f.forEach(function(p,pi){ if(pi===3) pts.push(p) })});
                  pts.forEach(function(p){ s+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="'+r+'" fill="'+OR+'"/>'; });
                  ARCS.slice(0,n==null?3:n).forEach(function(a){
                    s+='<path d="M'+(78+a[1])+' '+(44-a[2])+'A'+a[0]+' '+a[0]+' 0 0 1 '+(78+a[1])+' '+(44+a[2])+'" fill="none" stroke="'+OR+'" stroke-width="'+sw+'" stroke-linecap="round"/>';
                  });
                  return s;
                }
                function fav(n){
                  return '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="'+NV+'"/>'+
                    '<g transform="translate(-1 2) scale(.55)">'+mark(n)+'</g></svg>';
                }
                var link=document.querySelector('link[rel="icon"]');
                var step=0;
                setInterval(function(){
                  step=(step+1)%4;
                  if(document.hidden && link){
                    try{ link.href="data:image/svg+xml,"+encodeURIComponent(fav(step)); }catch(e){}
                  }
                },650);
                document.addEventListener("visibilitychange",function(){
                  if(!document.hidden && link) link.href="/icon.svg";
                });
              })();
            `,
          }}
        />
      </body>
    </html>
  );
}
