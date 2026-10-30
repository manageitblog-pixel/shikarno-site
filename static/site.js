document.addEventListener("click",function(e){
  var b=e.target.closest(".short-play"); if(!b) return;
  var box=b.closest(".short,.wide-video"), id=box.dataset.yt;
  var f=document.createElement("iframe");
  f.src="https://www.youtube-nocookie.com/embed/"+id+"?autoplay=1&rel=0";
  f.title="Відео ШІкарно"; f.allow="autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen=true;
  box.classList.add("on"); b.replaceWith(f);
});

/* Коментарі з Telegram: віджет вантажиться лише коли блок близько до екрана або по кліку — сторінка лишається швидкою */
(function(){
  var box=document.querySelector(".tg-comments"); if(!box) return;
  function load(){
    if(box.dataset.loaded) return; box.dataset.loaded="1";
    var dark=true;
    var s=document.createElement("script");
    s.async=true; s.src="https://telegram.org/js/telegram-widget.js?22";
    s.setAttribute("data-telegram-discussion", box.dataset.post);
    s.setAttribute("data-comments-limit","10");
    s.setAttribute("data-colorful","1");
    s.setAttribute("data-color", dark ? "FFD60A" : "6B47F5");
    if(dark) s.setAttribute("data-dark","1");
    box.innerHTML=""; box.appendChild(s);
  }
  box.addEventListener("click",function(e){ if(e.target.closest(".tg-load")) load(); });
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(en){ if(en[0].isIntersecting){ load(); io.disconnect(); } },{rootMargin:"400px"});
    io.observe(box);
  }
})();

/* Живий Байт: очі стежать за курсором (лише миша, без reduced-motion) */
(function(){
  var bots=[].slice.call(document.querySelectorAll(".bait.live")); if(!bots.length) return;
  if(!matchMedia("(pointer:fine)").matches||matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var x=0,y=0,raf=0;
  function look(){
    raf=0;
    bots.forEach(function(b){
      var r=b.getBoundingClientRect(); if(r.bottom<0||r.top>innerHeight) return;
      var dx=x-(r.left+r.width/2), dy=y-(r.top+r.height/2), d=Math.hypot(dx,dy)||1, k=Math.min(1,d/300);
      var e=b.querySelector(".b-eyes"); if(e) e.style.transform="translate("+(dx/d*4*k).toFixed(2)+"px,"+(dy/d*3*k).toFixed(2)+"px)";
    });
  }
  addEventListener("pointermove",function(ev){ x=ev.clientX; y=ev.clientY; if(!raf) raf=requestAnimationFrame(look); },{passive:true});
})();

/* Світіння картки йде за курсором */
(function(){
  if(!matchMedia("(pointer:fine)").matches) return;
  document.addEventListener("pointermove",function(e){
    var c=e.target.closest&&e.target.closest(".row"); if(!c) return;
    var r=c.getBoundingClientRect();
    c.style.setProperty("--mx",(e.clientX-r.left)+"px"); c.style.setProperty("--my",(e.clientY-r.top)+"px");
  },{passive:true});
})();
