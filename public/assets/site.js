(function(){var b=document.querySelector('.nav-toggle'),n=document.getElementById('nav');if(!b||!n)return;
b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)});})();
