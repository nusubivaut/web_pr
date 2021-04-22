console.log('test');
small_pictures = document.querySelectorAll('.picture');
big_picture = document.getElementById('big_picture');

function small_picture_handler(event) {
    if (event.type == 'mouseover') {
        picture_src = event.target.attributes.src.value;
        big_picture.src = picture_src;
    } else if (event.type == 'click') {
        console.log(event.target)
    }
}
for (i = 0; i < small_pictures.length; i++) {
    small_pictures[i].addEventListener('mouseover', small_picture_handler);
    small_pictures[i].addEventListener('click', small_picture_handler);
}