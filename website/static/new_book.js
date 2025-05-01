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
      initialReviewsContainer.className = 'initial-reviews';
      reviewsContainer.appendChild(initialReviewsContainer);
      
      // Create hidden reviews container (for expanding)
      const hiddenReviewsContainer = document.createElement('div');
      hiddenReviewsContainer.className = 'hidden-reviews';
      hiddenReviewsContainer.style.display = 'none';
      reviewsContainer.appendChild(hiddenReviewsContainer);
      
      // Create and append review cards
      data.reviews.forEach((review, index) => {
        console.log(`Processing review #${index + 1}:`, review.name, review.rating_value);
        
        // Create review card element
        const card = createReviewCard(review, index);
        
        // Add to initial or hidden container based on index
        if (index < 5) {
          initialReviewsContainer.appendChild(card);
        } else {
          hiddenReviewsContainer.appendChild(card);
        }
      });
      
      // Only add the "Show All" button if there are more than 5 reviews
      if (data.reviews.length > 5) {
        const showMoreButton = document.createElement('button');
        showMoreButton.className = 'mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors duration-200';
        showMoreButton.textContent = 'Show All Reviews';
        showMoreButton.setAttribute('aria-expanded', 'false');
        
        showMoreButton.addEventListener('click', function() {
          const isExpanded = hiddenReviewsContainer.style.display !== 'none';
          
          if (isExpanded) {
            // Hide the reviews
            hiddenReviewsContainer.style.display = 'none';
            showMoreButton.textContent = 'Show All Reviews';
            showMoreButton.setAttribute('aria-expanded', 'false');
          } else {
            // Show the reviews
            hiddenReviewsContainer.style.display = 'block';
            showMoreButton.textContent = 'Show Less';
            showMoreButton.setAttribute('aria-expanded', 'true');
          }
        });
        
        reviewsContainer.appendChild(showMoreButton);
      }
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

/**
 * Creates a review card DOM element
 * @param {Object} review - The review data
 * @param {number} index - The review index
 * @returns {HTMLElement} - The review card element
 */
function createReviewCard(review, index) {
    // Create main card container
    const card = document.createElement('div');
    card.className = 'flex space-x-4 mb-4 p-4 border border-gray-100 rounded shadow-sm hover:shadow transition-shadow duration-200';

    // Reviewer avatar
    const img = document.createElement('img');
    img.className = 'h-12 w-12 rounded-full object-cover';
    img.alt = `${review.name || 'Anonymous'}'s avatar`;
    
    // Handle image properly - might be base64 encoded or URL path
    if (review.image_b64) {
        if (review.image_b64.startsWith('http') || review.image_b64.startsWith('/')) {
            // It's a URL path
            img.src = review.image_b64;
        } else {
            // It's a base64 encoded string
            img.src = `data:image/png;base64,${review.image_b64}`;
        }
    } else {
        img.src = '/static/default-avatar.png';  // fallback
        console.log('Using default avatar for review', index + 1);
    }
    
    // Add onerror handler to use default if image fails to load
    img.onerror = function() {
        console.log('Image failed to load, using default avatar');
        this.src = '/static/default-avatar.png';
        this.onerror = null; // Prevent infinite loop if default also fails
    };

    // Content container
    const body = document.createElement('div');
    body.className = 'flex-1';

    // Name + stars row
    const header = document.createElement('div');
    header.className = 'flex items-center space-x-2';
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'font-medium text-gray-800';
    nameSpan.textContent = review.name || 'Anonymous';

    // Star rating
    const stars = createStarRating(review.rating_value);
    
    header.append(nameSpan, stars);

    // Comment
    const comment = document.createElement('p');
    comment.className = 'mt-1 text-gray-700';
    comment.textContent = review.comments || '— no comment —';

    // Date
    const date = document.createElement('p');
    date.className = 'mt-1 text-xs text-gray-500';
    try {
        date.textContent = formatDate(review.created_at);
    } catch (e) {
        console.error('Error formatting date:', e);
        date.textContent = review.created_at || 'Unknown date';
    }

    // Assemble components
    body.append(header, comment, date);
    card.append(img, body);
    
    return card;
}

/**
 * Creates a star rating element
 * @param {number} rating - The star rating (1-5)
 * @returns {HTMLElement} - The star rating element
 */
function createStarRating(rating) {
    const stars = document.createElement('div');
    stars.className = 'flex';
    
    // Ensure rating is a number
    const numericRating = Number(rating) || 0;
    
    for (let i = 1; i <= 5; i++) {
        const star = document.createElement('i');
        
        if (i <= numericRating) {
            star.className = 'fas fa-star text-yellow-500 mr-1';
        } else {
            star.className = 'far fa-star text-yellow-400 mr-1';
        }
        
        stars.appendChild(star);
    }

    // Add numeric rating
    const ratingText = document.createElement('span');
    ratingText.className = 'ml-1 text-sm text-gray-600';
    ratingText.textContent = `${numericRating}/5`;
    stars.appendChild(ratingText);
    
    return stars;
}

/**
 * Formats a date string nicely
 * @param {string} dateStr - The date string
 * @returns {string} - Formatted date
 */
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
            month: 'short', 
            day: 'numeric' 
        };
        
        return date.toLocaleDateString(undefined, options);
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateStr;
    }
}