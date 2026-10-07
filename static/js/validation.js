// AcxiomCRM Client-Side Form Validation Module

document.addEventListener('DOMContentLoaded', function () {
    // 1. Attach validation handlers to all forms with data-validate="true" or class "needs-validation"
    const forms = document.querySelectorAll('.needs-validation, form[data-validate="true"]');

    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            let isValid = true;

            // Clear previous errors
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            form.querySelectorAll('.custom-feedback').forEach(el => el.remove());

            // Validate Required Fields
            const requiredInputs = form.querySelectorAll('[required]');
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    showValidationError(input, 'This field is mandatory.');
                    isValid = false;
                }
            });

            // Validate Email Fields
            const emailInputs = form.querySelectorAll('input[type="email"], input[name="email"]');
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            emailInputs.forEach(input => {
                if (input.value.trim() && !emailRegex.test(input.value.trim())) {
                    showValidationError(input, 'Enter a valid email address (e.g. name@domain.com).');
                    isValid = false;
                }
            });

            // Validate Phone Fields
            const phoneInputs = form.querySelectorAll('input[name="phone"]');
            const phoneRegex = /^[0-9\+\-\s\(\)]{7,20}$/;
            phoneInputs.forEach(input => {
                if (input.value.trim() && !phoneRegex.test(input.value.trim())) {
                    showValidationError(input, 'Enter a valid phone number (min 7 digits).');
                    isValid = false;
                }
            });

            // Validate Opportunity Rules
            const amountInput = form.querySelector('input[name="amount"]');
            if (amountInput) {
                const val = parseFloat(amountInput.value);
                const stageSelect = form.querySelector('select[name="stage"]');
                const isLost = stageSelect && stageSelect.value === 'Lost';
                if (!isLost && (isNaN(val) || val <= 0)) {
                    showValidationError(amountInput, 'Opportunity Amount must be greater than 0.');
                    isValid = false;
                }
            }

            const probInput = form.querySelector('input[name="probability"]');
            if (probInput) {
                const prob = parseInt(probInput.value);
                if (isNaN(prob) || prob < 0 || prob > 100) {
                    showValidationError(probInput, 'Probability must be between 0 and 100.');
                    isValid = false;
                }
            }

            const closeDateInput = form.querySelector('input[name="expected_close_date"]');
            if (closeDateInput && closeDateInput.value) {
                const selectedDate = new Date(closeDateInput.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const stageSelect = form.querySelector('select[name="stage"]');
                const isLost = stageSelect && stageSelect.value === 'Lost';

                if (!isLost && selectedDate < today) {
                    showValidationError(closeDateInput, 'Expected Close Date cannot be in the past.');
                    isValid = false;
                }
            }

            // Validate Follow-Up Date Rule
            const followupDateInput = form.querySelector('input[name="followup_date"]');
            if (followupDateInput && followupDateInput.value) {
                const selectedDate = new Date(followupDateInput.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (selectedDate < today) {
                    showValidationError(followupDateInput, 'Follow-up date cannot be earlier than today.');
                    isValid = false;
                }
            }

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
        }, false);
    });

    function showValidationError(element, message) {
        element.classList.add('is-invalid');
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback custom-feedback d-block';
        feedback.innerText = message;
        element.parentNode.appendChild(feedback);
    }
});
