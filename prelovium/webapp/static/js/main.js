document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const onlineAd = document.getElementById('onlineAd');

    // Handle example selection
    document.querySelectorAll('.example-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const exampleType = this.dataset.example;
            
            // Show loading state
            loading.classList.remove('hidden');
            
            try {
                // Show original example images in preview containers
                const imageTypes = ['primary', 'secondary', 'label'];
                imageTypes.forEach((type, index) => {
                    const previewContainer = document.querySelectorAll('.preview-container')[index];
                    const preview = previewContainer.querySelector('img');
                    preview.src = `/examples/${exampleType}/${type}`;
                    previewContainer.classList.remove('hidden');
                });

                // Load example images
                const response = await fetch('/process', {
                    method: 'POST',
                    body: JSON.stringify({
                        example: exampleType
                    }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to process example images');
                }

                const data = await response.json();
                
                // Display results
                document.querySelectorAll('.result-image img').forEach((img, index) => {
                    const key = ['primary', 'secondary', 'label'][index];
                    img.src = data[key];
                });

                // Display online ad
                onlineAd.innerHTML = renderOnlineAd(data.metadata);
                
                // Show results section
                results.classList.remove('hidden');
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to load example images. Please try again.');
            } finally {
                loading.classList.add('hidden');
            }
        });
    });

    // Handle file upload form
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        // Show loading state
        loading.classList.remove('hidden');
        
        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to process images');
            }

            const data = await response.json();
            
            // Display results
            document.querySelectorAll('.result-image img').forEach((img, index) => {
                const key = ['primary', 'secondary', 'label'][index];
                img.src = data[key];
            });

            // Display online ad
            onlineAd.innerHTML = renderOnlineAd(data.metadata);
            
            // Show results section
            results.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to process images. Please try again.');
        } finally {
            loading.classList.add('hidden');
        }
    });

    // Handle image preview
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                const previewContainer = this.closest('.upload-container').querySelector('.preview-container');
                const preview = previewContainer.querySelector('img');
                
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    previewContainer.classList.remove('hidden');
                }
                
                reader.readAsDataURL(file);
            }
        });
    });
});

// Helper function to render metadata as HTML
function renderOnlineAd(m) {
    if (!m) return '';
    return `
        <div class="space-y-2">
            <h2 class="text-2xl font-bold text-gray-800">${m.title}</h2>
            <div class="flex flex-wrap items-center gap-4">
                <span class="inline-block bg-blue-100 text-blue-800 text-lg font-semibold px-3 py-1 rounded">€${m.price}</span>
                <span class="inline-block bg-gray-100 text-gray-800 px-3 py-1 rounded">Size: ${m.size}</span>
                <span class="inline-block bg-yellow-100 text-yellow-800 px-3 py-1 rounded">${(m.categories||[]).join(', ')}</span>
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <span class="font-medium">Colors:</span>
                ${(m.colors||[]).map(color => `<span class='inline-block w-4 h-4 rounded-full border border-gray-300' style='background:${color}' title='${color}'></span>`).join(' ')}
            </div>
            <div><span class="font-medium">Materials:</span> ${(m.materials||[]).join(', ')}</div>
            <div>
                <span class="font-medium">Brand:</span> 
                ${m.brand_domain && m.brand_domain !== 'NA' ? `<a href='https://${m.brand_domain}' class='text-blue-600 underline' target='_blank'>${m.brand}</a>` : m.brand}
            </div>
            <p class="mt-2 text-gray-700">${m.description}</p>
        </div>
    `;
} 