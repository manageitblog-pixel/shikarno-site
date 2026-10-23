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
    var dark=window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches;
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
