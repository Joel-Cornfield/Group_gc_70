document.addEventListener('DOMContentLoaded', function () {
    const friendsList = document.getElementById('friends-list');
    const friendsCount = document.getElementById('friends-count');
    const addFriendButton = document.getElementById('add-friend-button');
    const friendUsernameInput = document.getElementById('friend-username');
    const friendRequestsList = document.getElementById('friend-requests-list');
    const notificationList = document.getElementById('notification-list');
    const notificationBadge = document.querySelector('.notification-badge');
    const notificationCount = document.querySelector('.notification-count');
    const markAllReadBtn = document.querySelector('.mark-all-read');
    const emptyNotification = document.querySelector('.empty-notification');
    
    // Create notification container if it doesn't exist
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        const containerHTML = `
            <div id="notification-container" class="toast-container position-fixed top-0 end-0 p-3"></div>
        `;
        document.body.insertAdjacentHTML('beforeend', containerHTML);
        notificationContainer = document.getElementById('notification-container');
    }
    
    // Store notifications in memory
    let notifications = [];
    let unreadCount = 0;
    
    // Initialize Socket.IO connection
    const socket = io();
    
    // Socket.IO event listeners
    socket.on('connect', function() {
        console.log('Connected to WebSocket server');
        
        // Request any missed notifications after connection
        fetchInitialNotifications();
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket server');
    });
    
    // Listen for notifications
    socket.on('notification', function(data) {
        console.log('Notification received:', data);
        
        if (data.type === 'initial_notifications') {
            // Handle initial notifications
            data.data.forEach(notification => {
                addNotification(notification, false); // Don't animate for initial load
            });
            updateNotificationList();
            updateUnreadCount();
        } else {
            // Handle other types of notifications
            addNotification(data);
            
            switch(data.type) {
                case 'friend_request':
                    showNotification('New Friend Request', `${data.data.sender_name} sent you a friend request!`);
                    loadFriendRequests(); // Reload friend requests list
                    break;
                    
                case 'friend_accepted':
                    showNotification('Friend Request Accepted', `You are now friends with ${data.data.friend_name}!`);
                    loadFriends(); // Reload friends list
                    break;
                    
                case 'friend_rejected':
                    showNotification('Friend Request Rejected', `${data.data.username} rejected your friend request.`);
                    break;
                    
                case 'friend_removed':
                    showNotification('Friend Removed', `${data.data.username} is no longer your friend.`);
                    loadFriends(); // Reload friends list
                    break;
            }
        }
    });

    // Fetch initial notifications from server
    function fetchInitialNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                // Clear existing notifications
                notifications = [];
                
                // Add each notification to our list
                data.forEach(notification => {
                    addNotification(notification, false); // Don't animate for initial load
                });
                
                // Update the UI
                updateNotificationList();
                updateUnreadCount();
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }

    // Add a notification to the dropdown
    function addNotification(data, animate = true) {
        // Create notification object
        const notification = {
            id: data.id || Date.now(),
            type: data.type,
            title: getNotificationTitle(data.type),
            message: getNotificationMessage(data),
            icon: getNotificationIcon(data.type),
            time: data.created_at ? new Date(data.created_at) : new Date(),
            read: data.is_read || false
        };
        
        // Add to notifications array (at the beginning)
        notifications.unshift(notification);
        
        // Update the notification list in UI
        updateNotificationList();
        
        // Update unread count
        updateUnreadCount();
        
        // Animate the bell icon
        if (animate) {
            animateNotificationBell();
        }
    }
    
    // Get notification title based on type
    function getNotificationTitle(type) {
        switch(type) {
            case 'friend_request': return 'Friend Request';
            case 'friend_accepted': return 'Friend Request Accepted';
            case 'friend_rejected': return 'Friend Request Rejected';
            case 'friend_removed': return 'Friend Removed';
            default: return 'Notification';
        }
    }
    
    // Get notification message based on data
    function getNotificationMessage(data) {
        switch(data.type) {
            case 'friend_request': 
                return `${data.data.sender_name} sent you a friend request.`;
            case 'friend_accepted': 
                return `You are now friends with ${data.data.friend_name}.`;
            case 'friend_rejected': 
                return `${data.data.username} rejected your friend request.`;
            case 'friend_removed': 
                return `${data.data.username} is no longer your friend.`;
            default: 
                return data.message || 'You have a new notification.';
        }
    }
    
    // Get icon class based on notification type
    function getNotificationIcon(type) {
        switch(type) {
            case 'friend_request': return 'bi-person-plus-fill';
            case 'friend_accepted': return 'bi-person-check-fill';
            case 'friend_rejected': return 'bi-person-x-fill';
            case 'friend_removed': return 'bi-person-dash-fill';
            default: return 'bi-bell-fill';
        }
    }
    
    // Update the notification list in the UI
    function updateNotificationList() {
        // Guard against missing elements
        if (!notificationList) return;

        // Hide empty notification message if we have notifications
        if (notifications.length > 0 && emptyNotification) {
            emptyNotification.style.display = 'none';
        } else if (emptyNotification) {
            emptyNotification.style.display = 'block';
        }
        
        // Clear current list (except for the empty message)
        while (notificationList.firstChild) {
            if (notificationList.firstChild.classList && notificationList.firstChild.classList.contains('empty-notification')) {
                break;
            }
            notificationList.removeChild(notificationList.firstChild);
        }
        
        // Add notifications to the list
        notifications.forEach(notification => {
            const notificationItem = document.createElement('div');
            notificationItem.classList.add('notification-item', 'd-flex', 'align-items-start', 'p-2', 'border-bottom');
            if (!notification.read) {
                notificationItem.classList.add('unread', 'bg-light');
            }
            
            // Format the time
            const timeString = formatNotificationTime(notification.time);
            
            notificationItem.innerHTML = `
                <div class="notification-icon me-2">
                    <i class="bi ${notification.icon} fs-5"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-medium">${notification.title}</div>
                    <div class="notification-content small">${notification.message}</div>
                    <div class="notification-time text-muted small">${timeString}</div>
                </div>
                ${!notification.read ? '<div class="notification-dot bg-primary rounded-circle"></div>' : ''}
            `;
            
            // Add click event to mark as read
            notificationItem.addEventListener('click', () => {
                markNotificationAsRead(notification.id);
            });
            
            // Insert at the top, before the empty notification message
            notificationList.insertBefore(notificationItem, notificationList.firstChild);
        });
    }
    
    // Format notification time (e.g., "2 minutes ago")
    function formatNotificationTime(time) {
        const now = new Date();
        const diff = Math.floor((now - time) / 1000); // difference in seconds
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        return `${Math.floor(diff / 86400)} days ago`;
    }
    
    // Mark a notification as read
    function markNotificationAsRead(notificationId) {
        const notification = notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            updateUnreadCount();
            updateNotificationList();
            
            // Send to server to mark read
            fetch('/api/notifications/mark-read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notification_id: notificationId })
            }).catch(error => console.error('Error marking notification as read:', error));
        }
    }
    
    // Mark all notifications as read
    function markAllNotificationsAsRead() {
        notifications.forEach(notification => {
            notification.read = true;
        });
        updateUnreadCount();
        updateNotificationList();
        
        // Send to server to mark all read
        fetch('/api/notifications/mark-all-read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        }).catch(error => console.error('Error marking all notifications as read:', error));
    }
    
    // Update the unread notification count
    function updateUnreadCount() {
        unreadCount = notifications.filter(n => !n.read).length;
        
        if (unreadCount > 0 && notificationBadge) {
            notificationCount.textContent = unreadCount > 99 ? '99+' : unreadCount;
            notificationBadge.style.display = 'block';
        } else if (notificationBadge) {
            notificationBadge.style.display = 'none';
        }
    }
    
    // Animate the notification bell
    function animateNotificationBell() {
        const bell = document.querySelector('#notificationBell i');
        if (bell) {
            bell.classList.add('notification-pulse');
            setTimeout(() => {
                bell.classList.remove('notification-pulse');
            }, 1000);
        }
    }
    
    // Mark all as read button click event
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            markAllNotificationsAsRead();
        });
    }

    // Show notification toast
    function showNotification(title, message) {
        // Make sure notification container exists
        if (!notificationContainer) {
            console.error('Creating notification container');
            const containerHTML = `
                <div id="notification-container" class="toast-container position-fixed top-0 end-0 p-3"></div>
            `;
            document.body.insertAdjacentHTML('beforeend', containerHTML);
            notificationContainer = document.getElementById('notification-container');
        }
        
        // Create toast notification
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong>
                        <div>${message}</div>
                    </div>
                    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        // Add to notification container
        notificationContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Initialize and show the toast
        const toastElement = new bootstrap.Toast(document.getElementById(toastId), {
            autohide: true,
            delay: 5000
        });
        toastElement.show();
        
        // Optional: Play notification sound
        playNotificationSound();
    }
    
    // Play notification sound
    function playNotificationSound() {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.5;
        audio.play().catch(e => console.log('Error playing notification sound:', e));
    }

    // Fetch and display the friends list
    function loadFriends() {
        fetch('/api/friends')
            .then(response => response.json())
            .then(data => {
                if (!friendsList) return;
                
                friendsList.innerHTML = '';
                if (friendsCount) {
                    friendsCount.textContent = data.length;
                }

                if (data.length === 0) {
                    friendsList.innerHTML = '<li class="list-group-item text-center">You haven\'t added any friends yet</li>';
                    return;
                }

                data.forEach(friend => {
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
                    listItem.innerHTML = `
                        <div class="d-flex align-items-center">
                            <img src="${friend.profile_picture}" alt="Friend Avatar" class="me-3" style="width: 45px; height: 45px; border-radius: 50%;">
                            <div>
                                <a href="/analyticpage/${friend.id}" class="fw-medium">${friend.name}</a>
                            </div>
                        </div>
                        <button class="btn btn-outline-danger btn-sm remove-friend-button" data-friend-id="${friend.id}">
                            <i class="bi bi-person-x"></i>
                        </button>
                    `;
                    friendsList.appendChild(listItem);
                });
                
                // Add event listeners to remove friend buttons
                document.querySelectorAll('.remove-friend-button').forEach(button => {
                    button.addEventListener('click', function() {
                        const friendId = this.getAttribute('data-friend-id');
                        removeFriend(friendId);
                    });
                });
            })
            .catch(error => console.error('Error fetching friends:', error));
    }

    // Fetch and display pending friend requests
    function loadFriendRequests() {
        fetch('/api/friends/requests')
            .then(response => response.json())
            .then(data => {
                if (!friendRequestsList) return;
                
                friendRequestsList.innerHTML = '';

                if (data.length === 0) {
                    friendRequestsList.innerHTML = '<li class="list-group-item text-center">No pending requests</li>';
                    return;
                }

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
                        <div>
                            <button class="btn btn-success btn-sm accept-request-button me-1" data-request-id="${request.id}">
                                <i class="bi bi-check"></i> Accept
                            </button>
                            <button class="btn btn-danger btn-sm reject-request-button" data-request-id="${request.id}">
                                <i class="bi bi-x"></i> Reject
                            </button>
                        </div>
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
                
                // Add event listeners to reject buttons
                document.querySelectorAll('.reject-request-button').forEach(button => {
                    button.addEventListener('click', function () {
                        const requestId = this.getAttribute('data-request-id');
                        rejectFriendRequest(requestId);
                    });
                });
            })
            .catch(error => console.error('Error fetching friend requests:', error));
    }

    // Handle adding a new friend
    if (addFriendButton) {
        addFriendButton.addEventListener('click', function () {
            const username = friendUsernameInput.value.trim();
            if (!username) {
                showNotification('Error', 'Please enter a username.');
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
                        showNotification('Error', data.error);
                    } else {
                        showNotification('Success', data.message);
                        friendUsernameInput.value = '';
                        loadFriends(); // In case a pending request was auto-accepted
                    }
                })
                .catch(error => console.error('Error adding friend:', error));
        });
    }

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
                    showNotification('Error', data.error);
                } else {
                    showNotification('Success', data.message);
                    // Update UI immediately instead of reloading
                    const requestElement = document.querySelector(`.accept-request-button[data-request-id="${requestId}"]`).closest('li');
                    if (requestElement) {
                        requestElement.remove();
                    }
                    
                    // Add the friend to the friends list if we have friend data
                    if (data.friend && friendsList) {
                        const newFriend = data.friend;
                        const listItem = document.createElement('li');
                        listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
                        listItem.innerHTML = `
                            <div class="d-flex align-items-center">
                                <img src="${newFriend.profile_picture}" alt="Friend Avatar" class="me-3" style="width: 45px; height: 45px; border-radius: 50%;">
                                <div>
                                    <a href="/analyticpage/${newFriend.id}" class="fw-medium">${newFriend.name}</a>
                                </div>
                            </div>
                            <button class="btn btn-outline-danger btn-sm remove-friend-button" data-friend-id="${newFriend.id}">
                                <i class="bi bi-person-x"></i>
                            </button>
                        `;
                        friendsList.appendChild(listItem);
                        
                        // Update friends count
                        if (friendsCount) {
                            const currentCount = parseInt(friendsCount.textContent || '0');
                            friendsCount.textContent = currentCount + 1;
                        }
                        
                        // Add event listener to the new remove button
                        listItem.querySelector('.remove-friend-button').addEventListener('click', function() {
                            removeFriend(newFriend.id);
                        });
                    }
                    
                    // If there are no more requests, add the "No pending requests" message
                    if (friendRequestsList && friendRequestsList.children.length === 0) {
                        friendRequestsList.innerHTML = '<li class="list-group-item text-center">No pending requests</li>';
                    }
                }
            })
            .catch(error => console.error('Error accepting friend request:', error));
    }
    
    // Reject a friend request
    function rejectFriendRequest(requestId) {
        fetch('/api/friends/reject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification('Error', data.error);
                } else {
                    showNotification('Success', data.message);
                    // Remove the request from the UI without reloading
                    const requestElement = document.querySelector(`.reject-request-button[data-request-id="${requestId}"]`).closest('li');
                    if (requestElement) {
                        requestElement.remove();
                    }
                    
                    // If there are no more requests, add the "No pending requests" message
                    if (friendRequestsList && friendRequestsList.children.length === 0) {
                        friendRequestsList.innerHTML = '<li class="list-group-item text-center">No pending requests</li>';
                    }
                }
            })
            .catch(error => console.error('Error rejecting friend request:', error));
    }
    
    // Remove a friend
    function removeFriend(friendId) {
        if (confirm("Are you sure you want to remove this friend?")) {
            fetch('/api/friends/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ friend_id: friendId })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification('Error', data.error);
                    } else {
                        showNotification('Success', data.message);
                        // Remove the friend from the UI without reloading
                        const friendElement = document.querySelector(`.remove-friend-button[data-friend-id="${friendId}"]`).closest('li');
                        if (friendElement) {
                            friendElement.remove();
                        }
                        
                        // Update friends count
                        if (friendsCount) {
                            const currentCount = parseInt(friendsCount.textContent || '0');
                            friendsCount.textContent = Math.max(0, currentCount - 1);
                        }
                        
                        // If no more friends, show message
                        if (friendsList && friendsList.children.length === 0) {
                            friendsList.innerHTML = '<li class="list-group-item text-center">You haven\'t added any friends yet</li>';
                        }
                    }
                })
                .catch(error => console.error('Error removing friend:', error));
        }
    }

    // Initial load
    loadFriends();
    loadFriendRequests();
    fetchInitialNotifications(); // Load initial notifications
});