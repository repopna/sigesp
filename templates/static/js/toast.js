setTimeout(function(){
    if($('#msg').length > 0) {
        $('#msg').remove();
    }
}, 2000)

function fecharToast() {
    var toast = document.getElementById('toast');
    toast.style.display = 'none';
}