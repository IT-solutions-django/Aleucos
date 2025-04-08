var didScroll;    
var lastScrollTop = 0;    
var delta = 5;    
var navbarHeight = document.querySelector('.header').offsetHeight;    
console.log(navbarHeight)


function onScroll() {        
    didScroll = true;    
}


window.addEventListener('scroll', onScroll);    

setInterval(function() {        
    if (didScroll) {            
        hasScrolled();            
        didScroll = false;        
    }    
}, 150);    

function hasScrolled() {  
    let nav = document.querySelector('.header');      
    if (nav && nav.classList.contains('active')) {
        return;
    }

    var st = window.pageYOffset || document.documentElement.scrollTop;  

    // Проверяем, изменился ли scroll больше, чем delta
    if(Math.abs(lastScrollTop - st) <= delta)            
        return;        

    // Скрыть хедер при прокрутке вниз
    if (st > lastScrollTop && st > navbarHeight){     
        document.querySelector('.header').classList.remove('nav-down');
        document.querySelector('.header').classList.add('nav-up'); 

        // Закрываем мобильное меню, если оно открыто
        const navbarNav = document.getElementById('navbarNav');
        if (navbarNav) {
            navbarNav.classList.remove('show');
        }
    } 
    // Показать хедер при прокрутке вверх
    else {            
        if(st + window.innerHeight < document.body.scrollHeight) {                
            document.querySelector('.header').classList.remove('nav-up');
            document.querySelector('.header').classList.add('nav-down');            
        }        
    }     
    lastScrollTop = st;    
}