function updateSliderValue(sliderId, labelId) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(labelId);
    label.textContent = slider.value;
}

function selectOption(button) {
    const buttons = button.parentElement.querySelectorAll('button');
    buttons.forEach(btn => btn.classList.remove('selected'));
    button.classList.add('selected');

    // Simpan nilai tombol yang dipilih ke input tersembunyi
    const hiddenInput = document.getElementById(button.name + 'Value');
    hiddenInput.value = button.value;

    // Sembunyikan pesan error jika ada
    const errorMessage = document.getElementById(button.name + 'Error');
    if (errorMessage) {
        errorMessage.style.display = 'none';
    }
}

function validateForm() {
    let isValid = true;

    // Validasi Fluency
    const fluencyValue = document.getElementById('fluencyValue').value;
    if (fluencyValue === '0' || !fluencyValue) {
        document.getElementById('fluencyError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('fluencyError').style.display = 'none';
    }

    // Validasi Adequacy
    const adequacyValue = document.getElementById('adequacyValue').value;
    if (adequacyValue === '0' || !adequacyValue) {
        document.getElementById('adequacyError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('adequacyError').style.display = 'none';
    }

    return isValid;
}

// Tambahkan event listener untuk form submission
document.querySelector('form').addEventListener('submit', function (event) {
    if (!validateForm()) {
        event.preventDefault(); // Mencegah form dikirim jika tidak valid
    }
});