// updateUrl を Django から受け取る
var updateUrl = window.updateUrl; 

$(document).ready(function () {
    function sendAjaxUpdate(row, col, value) {
        if (!row || !col) {
            console.error("AJAX Error: row or col is missing", row, col);
            return;
        }

        $.ajax({
            url: updateUrl,  // DjangoのURLを利用
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
            data: {
                'row_id': row,
                'col_number': col,
                'value': value,
            },
            success: function (response) {
                if (response.success) {
                    for (const [colNumber, colValue] of Object.entries(response.updated_cells)) {
                        $(`td[data-row="${row}"][data-col="${colNumber}"]`).text(colValue);
                    }
                } else {
                    alert("Failed to update cell. Please try again.");
                }
            },
            error: function (xhr, status, error) {
                console.error("AJAX error:", error, xhr.responseText);
                alert("An error occurred.");
            }
        });
    }
});

// CSRFトークンを取得する関数
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}