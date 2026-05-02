document.querySelectorAll('.like').forEach(like => {
    const icon = like.querySelector('.like-icon');
    const likeCountElement = like.querySelector('.like-count');
    const postId = likeCountElement?.id;

    like.addEventListener('click', () => {
        const isLiked = icon.classList.contains('liked');
        const url = isLiked ? '/unlike' : '/like';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                post_id: postId
            })
        })
        .then(response => {
            if (response.ok) {
                icon.classList.toggle('liked');
                icon.classList.add('animate');
                setTimeout(() => {
                    icon.classList.remove('animate');
                }, 150);
            }
        });
    });
});

