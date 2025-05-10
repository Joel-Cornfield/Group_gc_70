document.addEventListener('DOMContentLoaded', function () {
    const friendsList = document.getElementById('friends-list');
    const friendsCount = document.getElementById('friends-count');
    const addFriendButton = document.getElementById('add-friend-button');
    const friendUsernameInput = document.getElementById('friend-username');
    const friendRequestsList = document.getElementById('friend-requests-list');

    // Fetch and display the friends list
    function loadFriends() {
        fetch('/api/friends')
            .then(response => response.json())
            .then(data => {
                friendsList.innerHTML = '';
                friendsCount.textContent = data.length;

                data.forEach(friend => {
                    console.log(friend); // Debugging: Check the friend object
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
                    listItem.innerHTML = `
                        <div class="d-flex align-items-center">
                            <img src="${friend.profile_picture}" alt="Friend Avatar" class="me-3" style="width: 45px; height: 45px; border-radius: 50%;">
                            <div>
                                <a href="/analyticpage/${friend.id}" class="fw-medium">${friend.name}</a>
                            </div>
                        </div>
                    `;
                    friendsList.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error fetching friends:', error));
    }

    // Fetch and display pending friend requests
    function loadFriendRequests() {
        fetch('/api/friends/requests')
            .then(response => response.json())
            .then(data => {
                friendRequestsList.innerHTML = '';

                data.forEach(request => {
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
                    listItem.innerHTML = `
                        <div class="d-flex align-items-center">
                            <img src="${request.profile_picture}" alt="Friend Avatar" class="me-3" style="width: 45px; height: 45px; border-radius: 50%;">
                            <div>
                                <span class="fw-medium">${request.name}</span>
                            </div>
                        </div>
                        <button class="btn btn-success btn-sm accept-request-button" data-request-id="${request.id}">
                            Accept
                        </button>
                    `;
                    friendRequestsList.appendChild(listItem);
                });

                // Add event listeners to accept buttons
                document.querySelectorAll('.accept-request-button').forEach(button => {
                    button.addEventListener('click', function () {
                        const requestId = this.getAttribute('data-request-id');
                        acceptFriendRequest(requestId);
                    });
                });
            })
            .catch(error => console.error('Error fetching friend requests:', error));
    }

    // Handle adding a new friend
    addFriendButton.addEventListener('click', function () {
        const username = friendUsernameInput.value.trim();
        if (!username) {
            alert('Please enter a username.');
            return;
        }

        fetch('/api/friends/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert(data.message);
                    friendUsernameInput.value = '';
                }
            })
            .catch(error => console.error('Error adding friend:', error));
    });

    // Accept a friend request
    function acceptFriendRequest(requestId) {
        fetch('/api/friends/accept', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert(data.message);
                    loadFriendRequests(); // Reload the friend requests list
                    loadFriends(); // Reload the friends list
                }
            })
            .catch(error => console.error('Error accepting friend request:', error));
    }

    // Initial load
    loadFriends();
    loadFriendRequests();
});