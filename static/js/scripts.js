$(document).ready(function() {
    const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
    const sentimentChart = new Chart(sentimentCtx, {
        type: 'pie',
        data: {
            labels: ['Neutral', 'Positive', 'Negative'],
            datasets: [{
                label: 'Sentiment Distribution',
                data: [0, 0, 0],
                backgroundColor: ['#f1c40f', '#2ecc71', '#e74c3c']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
    console.log('Sentiment chart initialized');


    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Total',
                data: [],
                borderColor: '#0860F9',
                fill: false
            }, {
                label: 'Neutral',
                data: [],
                borderColor: '#f1c40f',
                fill: false,
                hidden: true // Default to hidden
            }, {
                label: 'Positive',
                data: [],
                borderColor: '#2ecc71',
                fill: false
            }, {
                label: 'Negative',
                data: [],
                borderColor: '#e74c3c',
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                xAxes: [{
                    type: 'time',
                    time: {
                        unit: 'month'
                    }
                }]
            },
            onClick: function(event) {
                const points = trendChart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);
                if (points.length > 0) {
                    const firstPoint = points[0];
                    const label = trendChart.data.labels[firstPoint.index];
                    const value = trendChart.data.datasets[firstPoint.datasetIndex].data[firstPoint.index];

                    console.log('Clicked point:', { label, value });

                    // Calculate the start date as the first day of the previous month
                    const parsedDate = new Date(label + "-01");
                    const startDate = new Date(parsedDate.getFullYear(), parsedDate.getMonth() - 1, 1);

                    // Calculate the end date as the last day of the next month
                    const endDate = new Date(parsedDate.getFullYear(), parsedDate.getMonth() + 2, 0);

                    const formattedStartDate = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}-01`;
                    const formattedEndDate = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${endDate.getDate()}`;

                    // Update date fields with start and end of the month
                    $('#start_date').val(formattedStartDate);
                    $('#end_date').val(formattedEndDate);

                    // Trigger the filterTable function to update the table based on the new date
                    filterTable();
                }
            }
        }
    });
    console.log('Trend chart initialized');

    function updateSentimentChart(data) {
        sentimentChart.data.datasets[0].data = [data.neutral, data.positive, data.negative];
        sentimentChart.update();
    }

    function updateTrendChart(data) {
        trendChart.data.labels = data.months;
        trendChart.data.datasets[0].data = data.total_counts;
        trendChart.data.datasets[1].data = data.neutral_counts;
        trendChart.data.datasets[2].data = data.positive_counts;
        trendChart.data.datasets[3].data = data.negative_counts;
        trendChart.update();
    }

      // Filter table and update charts
      function filterTable() {
        const filterParams = {
            topic: $('#topic').val(),
            sentiment: $('#sentiment').val(),
            search: $('#search').val(),
            start_date: $('#start_date').val(),
            end_date: $('#end_date').val(),
            timeFrame: $('#time-frame').val()
        };

        $.post('/filter', filterParams, function(data) {
            $('#table-container').html(data);
        }).fail(function() {
            alert("Error loading data. Please try again.");
        });

        $.post('/get_sentiment_data', filterParams, function(data) {
            updateSentimentChart(data);
        }).fail(function() {
            alert("Error updating chart. Please try again.");
        });

        $.post('/get_trend_data', filterParams, function(data) {
            updateTrendChart(data);
        }).fail(function() {
            alert("Error updating trend chart. Please try again.");
        });

        const queryString = $.param(filterParams);
        $('#wordcloud').attr('src', '/filtered_wordcloud?' + queryString);
    }
    
    $('#topic, #sentiment, #start_date, #end_date, #time-frame').change(filterTable);
    $('#search').on('input', filterTable);

    $('#target').change(function() {
        $('.overlay, .spinner').show();
        const target = $(this).val();

        $.post('/refresh', { target }, function() {
            location.reload();
        }).fail(function() {
            $('.overlay, .spinner').hide();
            alert("Error fetching new target's data. Please try again.");
        });
    });

    $('#refresh').click(function() {
        $('.overlay, .spinner').show();
        $.post('/refresh', function() {
            location.reload();
        }).fail(function() {
            $('.overlay, .spinner').hide();
            alert("Error refreshing data. Please try again.");
        });
    });

    $('#toggle-view').click(function() {
        $('#table-container, #trend-chart-container').toggle();
        const isTableVisible = $('#table-container').is(':visible');
        $('#time-frame').toggle(!isTableVisible);
        if (!isTableVisible) {
            const topic = $('#topic').val();
            const sentiment = $('#sentiment').val();
            const search = $('#search').val();
            $.post('/get_trend_data', { topic, sentiment, search }, function(data) {
                updateTrendChart(data);
            }).fail(function() {
                alert("Error updating trend chart. Please try again.");
            });
        }
    });

    $(document).on('click', '.keyword-link', function(event) {
        event.preventDefault();
        const keyword = $(this).data('keyword');
        $('#search').val(keyword);
        filterTable();
    });

    $('#clear-search').click(function() {
        $('#search, #start_date, #end_date, #topic, #sentiment').val('');
        $('#time-frame').val('M');
        filterTable();
    });

    $('#cancel-fetch').click(function() {
        $.post('/cancel', function() {}).fail(function() {
            alert("Error cancelling subprocess. Please try again.");
        });
    });

    $('#time-frame').hide();
    filterTable();
});