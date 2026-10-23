document.addEventListener("click",function(e){
  var b=e.target.closest(".short-play"); if(!b) return;
  var box=b.closest(".short"), id=box.dataset.yt;
  var f=document.createElement("iframe");
  f.src="https://www.youtube-nocookie.com/embed/"+id+"?autoplay=1&rel=0";
  f.title="Відео ШІкарно"; f.allow="autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen=true;
  box.classList.add("on"); b.replaceWith(f);
});
