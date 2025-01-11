function updateClock() {
    var now = new Date();
    
    // Define o fuso horário desejado (exemplo: UTC-3)
    var timezoneOffset = +1 * 60; // em minutos
    var utcOffset = now.getTimezoneOffset(); // offset do UTC em minutos
    
    var localTime = now.getTime() + (timezoneOffset + utcOffset) * 60 * 1000;
    var localDate = new Date(localTime);

    var hours = localDate.getHours();
    var minutes = localDate.getMinutes();
    var seconds = localDate.getSeconds();

    hours = hours < 10 ? '0' + hours : hours;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    seconds = seconds < 10 ? '0' + seconds : seconds;
    
    var timeString = hours + ':' + minutes + ':' + seconds;
    
    document.getElementById('clock').textContent = timeString;
}

setInterval(updateClock, 1000);