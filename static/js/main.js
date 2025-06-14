// Constants
const READER_LINE_CLASS = 'reader-line';

// Dark mode toggle
$('#darkModeToggle').on('change', function () {
    $('body').toggleClass('dark-mode');
});

// Column detection
$('#file').on('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const json = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
        const headers = json[0];

        const select = $('#column-select');
        select.empty().append('<option disabled selected>Select column</option>');
        headers.forEach(h => {
            if (h) select.append(`<option value="${h}">${h}</option>`);
        });
        $('#column-select-wrapper').show();
    };
    reader.readAsArrayBuffer(file);
});

// Update progress function
function updateProgress(current, total) {
    const progress = (current / total * 100).toFixed(1);
    $('#progress-bar').css('width', progress + '%').text(progress + '%');
    $('#progress-count').text(`Processing ${current} of ${total}`);

    if (progress >= 100) {
        $('#step-processing').removeClass('active').addClass('disabled');
        $('#step-done').removeClass('disabled').addClass('active');
    }
}

// Upload history
function updateHistory(historyData) {
    const container = $('#upload-history');
    container.empty();
    historyData.forEach(entry => {
        container.append(`
      <li class="list-group-item">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <strong>${entry.date}</strong>
            <br>
            <small class="text-muted">Total: ${entry.count} entries</small>
          </div>
          <div>
            <span class="badge bg-success">${entry.success_count}</span>
            <span class="badge bg-danger">${entry.error_count}</span>
            <span class="badge bg-warning">${entry.failed_count}</span>
          </div>
        </div>
      </li>
    `);
    });
}

// Load initial history
$.get('/history', function (data) {
    updateHistory(data);
});

// Submit form
$('#form').on('submit', function (e) {
    e.preventDefault();

    const url = $('#url').val();
    const file = $('#file')[0].files[0];
    const column = $('#column-select').val() || 'MATRIC';

    if (!url || !file) {
        $('#status').text('Please provide the website link and select an Excel file.');
        return;
    }

    const formData = new FormData();
    formData.append('url', url);
    formData.append('file', file);
    formData.append('column', column);

    $('#status').text('Uploading and starting process...');
    $('#progress-bar').css('width', '0%').text('0%');
    $('#progress-count').text('Processing 0 of 0');
    $('#progress-section').show();
    $('#success-count').text('0');
    $('#error-count').text('0');
    $('#failed-count').text('0');

    // Get the current hostname and port
    const apiUrl = '/process';

    $.ajax({
        url: apiUrl,
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response.error) {
                $('#status').text('Error: ' + response.error);
                return;
            }
            $('#status').text('Process started!');
            $('#step-upload').removeClass('active').addClass('disabled');
            $('#step-processing').removeClass('disabled').addClass('active');

            // Update counts
            const results = response.results;
            $('#success-count').text(results.filter(r => r.status === 'success').length);
            $('#error-count').text(results.filter(r => r.status === 'error').length);
            $('#failed-count').text(results.filter(r => r.status === 'failed').length);

            // Update history with the new data from response
            updateHistory(response.history);
        },
        error: function (xhr, status, error) {
            let errorMessage = 'An error occurred.';
            try {
                // Try to parse as JSON first
                const response = JSON.parse(xhr.responseText);
                errorMessage = response.error || response.details || errorMessage;
            } catch (e) {
                // If not JSON, check if it's HTML
                if (xhr.responseText.includes('<html>')) {
                    errorMessage = 'Server Error: The application might need to be restarted. Please contact administrator.';
                    console.error('Server returned HTML instead of JSON:', xhr.responseText);
                } else {
                    errorMessage = xhr.responseText || errorMessage;
                }
            }
            $('#status').text('Error: ' + errorMessage);
            console.error('Server error:', {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText
            });
        }
    });

    const progressUrl = '/progress';
    const interval = setInterval(() => {
        $.get(progressUrl, function (data) {
            const { progress, current, total } = data;
            updateProgress(current, total);
            if (progress >= 100) {
                clearInterval(interval);
                $('#status').text('✅ Process completed successfully!');
                $('#step-processing').removeClass('active').addClass('disabled');
                $('#step-done').removeClass('disabled').addClass('active');
            }
        }).fail(function (xhr, status, error) {
            console.error('Progress check failed:', error);
            clearInterval(interval);
            $('#status').text('Error: Failed to check progress');
        });
    }, 1000);
}); 