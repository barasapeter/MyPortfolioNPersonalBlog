const viewMode = document.getElementById('viewMode');
const editMode = document.getElementById('editMode');
const editBtn = document.getElementById('editBtn');
const cancelBtn = document.getElementById('cancelBtn');
const pageTitle = document.getElementById('pageTitle');
const profileForm = document.getElementById('profileForm');

const avatarInput = document.getElementById('avatarInput');
const avatarPreview = document.getElementById('avatarPreview');
const bioInput = document.getElementById('bioInput');
const charCount = document.getElementById('charCount');

editBtn.addEventListener('click', () => {
    viewMode.classList.add('hidden');
    editMode.classList.remove('hidden');
    editBtn.classList.add('hidden');
    pageTitle.textContent = 'Edit Profile';
});

cancelBtn.addEventListener('click', () => {
    editMode.classList.add('hidden');
    viewMode.classList.remove('hidden');
    editBtn.classList.remove('hidden');
    pageTitle.textContent = 'Profile';
});

avatarInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 2 * 1024 * 1024) {
            alert('File must be less than 2MB');
            e.target.value = '';
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            avatarPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

bioInput.addEventListener('input', () => {
    charCount.textContent = bioInput.value.length;
});

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `
        flex items-center gap-3
        px-4 py-3 rounded-lg shadow-lg
        text-sm font-medium
        transform transition-all duration-300
        opacity-0 translate-y-[-10px]
        ${type === 'success'
            ? 'bg-black text-white'
            : 'bg-red-600 text-white'}
    `;

    toast.innerHTML = `
        <span>${message}</span>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-[-10px]');
        toast.classList.add('opacity-100', 'translate-y-0');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = profileForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Updating...';
    submitBtn.classList.add('opacity-70', 'cursor-not-allowed');

    const formData = new FormData();
    formData.append('full_name', document.getElementById('fullNameInput').value);
    formData.append('username', document.getElementById('usernameInput').value);
    formData.append('email', document.getElementById('emailInput').value);
    formData.append('bio', bioInput.value);

    if (avatarInput.files[0]) {
        formData.append('avatar', avatarInput.files[0]);
    }

    try {
        const response = await fetch('/api/v1/update-profile', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Profile update failed');
        }

        showToast('Update success', 'success');

        editMode.classList.add('hidden');
        viewMode.classList.remove('hidden');
        editBtn.classList.remove('hidden');
        pageTitle.textContent = 'Profile';

        if (data.user?.avatar) {
            document.querySelectorAll('img').forEach(img => {
                if (img.id === 'avatarPreview' || img.alt === data.user.username) {
                    img.src = data.user.avatar + '?v=' + Date.now();
                }
            });
        }

    } catch (error) {
        console.error(error);
        showToast(error.message || 'Something went wrong', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        submitBtn.classList.remove('opacity-70', 'cursor-not-allowed');
    }
});
