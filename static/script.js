$(document).ready(function () {
  // Add or Update Expense
  $("#expense-form").submit(function (event) {
    event.preventDefault();
    const editId = $("#expense-form").attr("data-edit-id");
    const expenseData = {
      amount: $("#amount").val(),
      category: $("#category").val(),
      date: $("#date").val(),
      location: $("#location").val() || "Unknown",
      payment_mode: $("#payment-mode").val(),
    };

    if (editId) {
      // Update expense
      $.ajax({
        url: `/update_expense/${editId}`,
        type: "PUT",
        contentType: "application/json",
        data: JSON.stringify(expenseData),
        success: function (response) {
          alert(response.message);
          resetForm();
          loadExpenses();
        },
        error: function () {
          alert("Error updating expense.");
        },
      });
    } else {
      // Add expense
      $.ajax({
        url: "/add_expense",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(expenseData),
        success: function (response) {
          alert(response.message);
          resetForm();
          loadExpenses();
        },
        error: function () {
          alert("Error adding expense.");
        },
      });
    }
  });

  // Load Expenses
  function loadExpenses() {
    $.ajax({
      url: "/get_expenses",
      type: "GET",
      success: function (expenses) {
        $("#expense-list").empty();
        expenses.forEach((exp) => {
          $("#expense-list").append(`
            <li>
                <strong>${exp.category} - </strong> 
                <div class="info"> ₹${exp.amount} on ${exp.date} 
                📍 ${exp.location} | 💳 ${exp.payment_mode}</div>
                <button class="edit-expense" data-id="${exp.id}" 
                  data-amount="${exp.amount}" 
                  data-category="${exp.category}"
                  data-date="${exp.date}"
                  data-location="${exp.location}"
                  data-payment-mode="${exp.payment_mode}">
                  ✏️ Edit
                </button>
                <button class="delete-expense" data-id="${exp.id}">🗑️ Delete</button>
            </li>
          `);
        });
      },
      error: function () {
        console.log("Error loading expenses.");
      },
    });
  }
  loadExpenses();

  // Reset Form
  function resetForm() {
    $("#expense-form")[0].reset();
    $("#expense-form").removeAttr("data-edit-id");
    $("#submit-btn").text("Add Expense");
  }

  // Delete Expense
  $(document).on("click", ".delete-expense", function () {
    const id = $(this).data("id");
    if (confirm("Are you sure?")) {
      $.ajax({
        url: `/delete_expense/${id}`,
        type: "DELETE",
        success: function (response) {
          alert(response.message);
          loadExpenses();
        },
        error: function () {
          alert("Error deleting expense.");
        },
      });
    }
  });

  // Edit Expense
  $(document).on("click", ".edit-expense", function () {
    const id = $(this).data("id");
    $("#amount").val($(this).data("amount"));
    $("#category").val($(this).data("category"));
    $("#date").val($(this).data("date"));
    $("#location").val($(this).data("location"));
    $("#payment-mode").val($(this).data("payment-mode"));

    $("#expense-form").attr("data-edit-id", id);
    $("#submit-btn").text("Update Expense");
  });

  // Load Charts
  function loadCharts() {
    $.ajax({
      url: "/get_charts_data",
      type: "GET",
      success: function (data) {
        if (data.error) {
          console.log("No data available for charts.");
          return;
        }
        Plotly.newPlot("category-pie", JSON.parse(data.category_pie));
        Plotly.newPlot("expense-trend", JSON.parse(data.expense_trend));
        Plotly.newPlot("payment-mode-bar", JSON.parse(data.payment_mode_bar));
        Plotly.newPlot("category-trend", JSON.parse(data.category_trend));
        Plotly.newPlot("expense-heatmap", JSON.parse(data.expense_heatmap));
      },
      error: function () {
        console.log("Error loading charts.");
      },
    });
  }
  loadCharts();
  setInterval(loadCharts, 5000);

  // Chatbot Functionality
  $("#send-btn").click(function () {
    let userMessage = $("#chat-input").val().trim();
    if (userMessage === "") return;

    $("#chat-messages").append(
      `<div class="message user-message">🧑‍💻 ${userMessage}</div>`
    );
    $("#chat-input").val("");
    $("#chat-box").animate({ scrollTop: $("#chat-box")[0].scrollHeight }, 500);

    $.ajax({
      url: "/chatgpt_insights",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ question: userMessage }),
      success: function (data) {
        let botMessage = data.error ? "No insights available!" : data.insights;
        $("#chat-messages").append(
          `<div class="message bot-message">🤖 ${botMessage}</div>`
        );
        $("#chat-box").animate(
          { scrollTop: $("#chat-box")[0].scrollHeight },
          500
        );
      },
      error: function () {
        $("#chat-messages").append(
          `<div class="message bot-message">🤖 Error fetching insights.</div>`
        );
      },
    });
  });
});
