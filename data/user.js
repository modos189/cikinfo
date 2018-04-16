(function (d, w, c) {
    (w[c] = w[c] || []).push(function() {
        try {
            w.yaCounter47963423 = new Ya.Metrika2({
                id:47963423,
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true,
                ut:"noindex"
            });
        } catch(e) { }
    });

    var n = d.getElementsByTagName("script")[0],
        s = d.createElement("script"),
        f = function () { n.parentNode.insertBefore(s, n); };
    s.type = "text/javascript";
    s.async = true;
    s.src = "https://mc.yandex.ru/metrika/tag.js";

    if (w.opera == "[object Opera]") {
        d.addEventListener("DOMContentLoaded", f, false);
    } else { f(); }
})(document, window, "yandex_metrika_callbacks2");


function setCookie(name, value, options) {
  options = options || {};

  var expires = options.expires;

  if (typeof expires == "number" && expires) {
    var d = new Date();
    d.setTime(d.getTime() + expires * 1000);
    expires = options.expires = d;
  }
  if (expires && expires.toUTCString) {
    options.expires = expires.toUTCString();
  }

  value = encodeURIComponent(value);

  var updatedCookie = name + "=" + value;

  for (var propName in options) {
    updatedCookie += "; " + propName;
    var propValue = options[propName];
    if (propValue !== true) {
      updatedCookie += "=" + propValue;
    }
  }

  document.cookie = updatedCookie;
}


// возвращает cookie с именем name, если есть, если нет, то undefined
function getCookie(name) {
  var matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}


window.onload = function() {
    setTimeout(function() {

        var help = document.getElementById('help-wrapper');

        if (getCookie('again') === undefined) {
            help.className = 'help-wrapper help-wrapper__show';
            setCookie('again', true)
        }

        var btn = document.getElementById('left-button-help');
        btn.onclick = function() {
            help.className = 'help-wrapper help-wrapper__show';
        };

        var slides = document.querySelectorAll('#help .help-slide')
        var currentSlide = 0;
        var next = document.getElementById('help-next');
        var previous = document.getElementById('help-previous');

        function nextSlide() {
            if (currentSlide === 0) {
                previous.className = 'help-controls';
                previous.innerText = '<'
            }
            if (currentSlide === 6) {
                next.className = 'help-controls help-controls-ok';
                next.innerText = '✔'
            }
            if (currentSlide === 7) {
                next.className = 'help-controls';
                next.innerText = '>'
                previous.className = 'help-controls help-controls-close';
                previous.innerText = '❌'
            }

            if (currentSlide === 7) {
                help.className = 'help-wrapper';
            }
            goToSlide(currentSlide+1);
        }

        function previousSlide() {
            if (currentSlide === 1) {
                previous.className = 'help-controls help-controls-close';
                previous.innerText = '❌'
            }
            if (currentSlide === 7) {
                next.className = 'help-controls';
                next.innerText = '>'
            }

            if (currentSlide === 0) {
                help.className = 'help-wrapper';
            } else {
                goToSlide(currentSlide-1);
            }
        }

        function goToSlide(n) {
            slides[currentSlide].className = 'help-slide';
            currentSlide = (n+slides.length)%slides.length;
            slides[currentSlide].className = 'help-slide help-slide__showing';
        }

        next.onclick = function() {
            nextSlide();
        };
        previous.onclick = function() {
            previousSlide();
        };

    }, 1500)
};


