document.addEventListener('DOMContentLoaded', () => {
    const reviewsContainer = document.getElementById('reviewsContainer');
    
    if (!reviewsContainer) {
        console.error('Reviews container not found!');
        return;
    }
    
    // Debug information about the URL
    console.log('Reviews section initialized');
    
    if (!window.REVIEWS_URL) {
        console.error('REVIEWS_URL is not defined!');
        reviewsContainer.innerHTML = '<p class="text-red-500">Reviews URL not configured.</p>';
        return;
    }
    
    console.log('Attempting to fetch reviews from:', window.REVIEWS_URL);
    
    // Show loading state
    reviewsContainer.innerHTML = `<p class="text-gray-500">Loading reviews from ${window.REVIEWS_URL}...</p>`;
  
    // Fetch reviews data
    fetch(window.REVIEWS_URL, {
      credentials: 'same-origin'
    })
    .then(res => {
      console.log('Server response status:', res.status);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      console.log('Received data:', data);
      reviewsContainer.innerHTML = '';
      
      if (!data.success) {
        console.warn('Server reported failure:', data.message);
        reviewsContainer.innerHTML = `<p class="text-red-500">Server reported an error: ${data.message || 'Unknown error'}</p>`;
        return;
      }
      
      if (!data.reviews || !data.reviews.length) {
        console.log('No reviews available for this cottage');
        reviewsContainer.innerHTML = '<p class="text-gray-500">No reviews yet for this cottage.</p>';
        return;
      }
      
      console.log(`Displaying ${data.reviews.length} reviews`);
      
      // Create initial reviews container
      const initialReviewsContainer = document.createElement('div');
      initialReviewsContainer.className = 'space-y-6';
      reviewsContainer.appendChild(initialReviewsContainer);
      
      // Create and append review cards
      data.reviews.forEach((review, index) => {
        console.log(`Processing review #${index + 1}:`, review);
        console.log('User image data:', review.user_image ? 'Present' : 'Missing');
        
        // Create review card element
        const card = createReviewCard(review, index);
        initialReviewsContainer.appendChild(card);
      });
    })
    .catch(err => {
      console.error('Error fetching reviews:', err);
      reviewsContainer.innerHTML = `
        <div class="p-4 bg-red-50 text-red-700 rounded">
          <p class="font-bold">Failed to load reviews</p>
          <p>${err.message}</p>
          <p class="text-sm mt-2">Check your browser console for more details.</p>
        </div>
      `;
    });
});

function createReviewCard(review, index) {
    console.log('Creating review card for:', review);
    
    // Create main card container
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300';

    // Create avatar container
    const avatarContainer = document.createElement('div');
    avatarContainer.className = 'flex-shrink-0';

    // Handle user image
    if (review.user_image) {
        console.log('User image found, creating image element');
        const img = document.createElement('img');
        img.className = 'w-12 h-12 rounded-full object-cover border-2 border-gray-200';
        img.alt = `${review.user_name || 'Anonymous'}'s avatar`;
        
        // Set image source based on the type of data
        if (typeof review.user_image === 'string') {
            if (review.user_image.startsWith('data:')) {
                img.src = review.user_image;
            } else if (review.user_image.startsWith('http') || review.user_image.startsWith('/')) {
                img.src = review.user_image;
            } else {
                img.src = `data:image/jpeg;base64,${review.user_image}`;
            }
        }
        
        // Add error handling
        img.onerror = function() {
            console.log('Image failed to load, creating fallback avatar');
            const fallbackDiv = createFallbackAvatar(review.user_name);
            this.parentNode.replaceChild(fallbackDiv, this);
        };
        
        avatarContainer.appendChild(img);
    } else {
        console.log('No user image, creating fallback avatar');
        avatarContainer.appendChild(createFallbackAvatar(review.user_name));
    }

    // Create content container
    const contentContainer = document.createElement('div');
    contentContainer.className = 'flex-grow';

    // Create header with name and date
    const header = document.createElement('div');
    header.className = 'flex items-center justify-between mb-2';
    
    const nameSpan = document.createElement('h3');
    nameSpan.className = 'text-lg font-semibold text-gray-800';
    nameSpan.textContent = review.user_name || 'Anonymous';

    const dateSpan = document.createElement('span');
    dateSpan.className = 'text-sm text-gray-500';
    dateSpan.textContent = formatDate(review.date_created);

    header.append(nameSpan, dateSpan);

    // Create rating
    const ratingDiv = document.createElement('div');
    ratingDiv.className = 'flex items-center mb-2';
    ratingDiv.appendChild(createStarRating(review.rating));

    // Create comment
    const comment = document.createElement('p');
    comment.className = 'text-gray-600';
    comment.textContent = review.comment || '— no comment —';

    // Assemble the card
    contentContainer.append(header, ratingDiv, comment);
    
    const mainContainer = document.createElement('div');
    mainContainer.className = 'flex items-start space-x-4';
    mainContainer.append(avatarContainer, contentContainer);
    
    card.appendChild(mainContainer);
    
    return card;
}

function createFallbackAvatar(userName) {
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center';
    
    const initial = document.createElement('span');
    initial.className = 'text-gray-600 font-bold text-lg';
    initial.textContent = (userName || 'A').charAt(0).toUpperCase();
    
    avatarDiv.appendChild(initial);
    return avatarDiv;
}

function createStarRating(rating) {
    const stars = document.createElement('div');
    stars.className = 'flex items-center';
    
    // Ensure rating is a number
    const numericRating = Number(rating) || 0;
    
    // Create stars container
    const starsContainer = document.createElement('div');
    starsContainer.className = 'flex';
    
    for (let i = 1; i <= 5; i++) {
        const star = document.createElement('span');
        star.className = i <= numericRating ? 'text-yellow-400' : 'text-gray-300';
        star.textContent = i <= numericRating ? '★' : '☆';
        starsContainer.appendChild(star);
    }

    // Add numeric rating
    const ratingText = document.createElement('span');
    ratingText.className = 'ml-2 text-sm text-gray-600';
    ratingText.textContent = `${numericRating}/5`;
    
    stars.append(starsContainer, ratingText);
    return stars;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Unknown date';
    
    try {
        const date = new Date(dateStr);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateStr;
        }
        
        // Format options for date display
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        
        return date.toLocaleDateString(undefined, options);
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateStr;
    }
}