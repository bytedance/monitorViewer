$(document).ready(async function () {
    start_page_loading();

    init_datetime_picker();

    init_table_data();

    init_chart();

    is_data_ready();
});

window.onbeforeunload = function() {
    start_page_loading();
};

function start_page_loading() {
    localStorage.setItem("progress", 0)

    let progressBar = document.getElementById('progress-bar');
    progressBar.style.width = 0 + '%';
    progressBar.setAttribute('aria-valuenow', 0);

    document.getElementById('loading').style.display = 'block';
    document.body.insertAdjacentHTML('beforeend', '<div class="overlay"></div>');
}

function is_data_ready() {
    let totalData = 8;
    let dataLoaded = parseInt(localStorage.getItem("progress"));
    let progressBar = document.getElementById('progress-bar');
    let progress = (dataLoaded / totalData) * 100;
    progressBar.style.width = progress + '%';
    progressBar.setAttribute('aria-valuenow', progress);
    console.log(progress)

    // 检查是否加载完成
    if (dataLoaded < totalData) {
        // 如果还未加载完所有数据，则继续加载
        setTimeout(is_data_ready, 50); // 模拟加载延迟
    } else {
        document.getElementById('loading').style.display = 'none';
        document.querySelector('.overlay').remove();
    }
}

function init_chart() {
    $.get('/alarm_chart_data?begin_datetime=' + $('#begin_datetime').val() + '&end_datetime=' + $('#end_datetime').val(), function (response) {
        init_alarm_chart(response.categories, response.series)
    }).fail(function (xhr, status, error) {
        console.error('Error:', status, error);
    });

    $.get('/top_alarms_per_monitor_item?begin_datetime=' + $('#begin_datetime').val() + '&end_datetime=' + $('#end_datetime').val(), function (response) {
        init_monitor_chart(response.categories, response.series)
    }).fail(function (xhr, status, error) {
        console.error('Error:', status, error);
    });
}

function init_datetime_picker() {
    var currentDate = new Date();
    var currentFormattedDate = currentDate.getFullYear() + '-' +
        ('0' + (currentDate.getMonth() + 1)).slice(-2) + '-' +
        ('0' + currentDate.getDate()).slice(-2) + ' ' +
        ('0' + currentDate.getHours()).slice(-2) + ':' +
        ('0' + currentDate.getMinutes()).slice(-2) + ':' +
        ('0' + currentDate.getSeconds()).slice(-2);
    var oneDay = 7 * 24 * 60 * 60 * 1000; // 一天的毫秒数
    var lastDayDate = new Date(currentDate.getTime() - oneDay);
    var lastDayFormattedDate = lastDayDate.getFullYear() + '-' +
        ('0' + (lastDayDate.getMonth() + 1)).slice(-2) + '-' +
        ('0' + lastDayDate.getDate()).slice(-2) + ' ' +
        ('0' + lastDayDate.getHours()).slice(-2) + ':' +
        ('0' + lastDayDate.getMinutes()).slice(-2) + ':' +
        ('0' + lastDayDate.getSeconds()).slice(-2);
    if ($('#begin_datetime').val() == '') {
        $('#begin_datetime').val(lastDayFormattedDate);
    }
    if ($('#end_datetime').val() == '') {
        $('#end_datetime').val(currentFormattedDate);
    }
    let lastSelectedBeginDateTime = new Date($('#begin_datetime').val()).getTime();
    flatpickr('#begin_datetime', {
        enableTime: true, // 启用时间选择
        dateFormat: 'Y-m-d H:i:S', // 日期时间格式
        time_24hr: true, // 使用 24 小时制
        defaultDate: $('#begin_datetime').val(),
        enableSeconds: true, // 启用秒选
        onClose: function (selectedDates, dateStr, instance) {
            let newSelectedDateTime = selectedDates[0].getTime();
            // 判断所选日期时间是否有变化
            if (lastSelectedBeginDateTime !== newSelectedDateTime) {
                console.log("所选日期时间已发生变化！");
                lastSelectedBeginDateTime = newSelectedDateTime;
                window.location.href = '/?begin_datetime=' + $('#begin_datetime').val() + '&end_datetime=' + $('#end_datetime').val();
                start_page_loading();
            } else {
                console.log("所选日期时间未变化。");
            }
        }
    });
    let lastSelectedEndDateTime = new Date($('#end_datetime').val()).getTime();
    flatpickr('#end_datetime', {
        enableTime: true, // 启用时间选择
        dateFormat: 'Y-m-d H:i:S', // 日期时间格式
        time_24hr: true, // 使用 24 小时制
        defaultDate: $('#end_datetime').val(),
        enableSeconds: true, // 启用秒选
        onClose: function (selectedDates, dateStr, instance) {
            let newSelectedDateTime = selectedDates[0].getTime();
            // 判断所选日期时间是否有变化
            if (lastSelectedEndDateTime !== newSelectedDateTime) {
                console.log("所选日期时间已发生变化！");
                // 在这里处理日期时间变化的逻辑
                lastSelectedEndDateTime = newSelectedDateTime;
                window.location.href = '/?begin_datetime=' + $('#begin_datetime').val() + '&end_datetime=' + $('#end_datetime').val();
                start_page_loading();
            } else {
                console.log("所选日期时间未变化。");
            }
        }
    });
}

function init_table_data() {
    let monitor_table = $('#monitor-details-table').DataTable({
        responsive: true,
        "processing": true,
        "serverSide": false,
        ordering: false,
        "ajax": {
            "url": "/monitor_table_data",
            "type": "GET",
            "data": function (d) {
                d.start = d.start || 0;  // 初始记录索引
                d.length = d.length || 10;  // 页面大小
                d.draw = d.draw || 1;  // 绘制计数器
                d.search = d.search || '';  // 搜索值
                d.order = d.order || [{'column': 0, 'dir': 'asc'}];  // 排序
                d.begin_datetime = $('#begin_datetime').val();
                d.end_datetime = $('#end_datetime').val();
            }
        },
        "columns": [
            {"data": "direction"},
            {"data": "admin"},
            {"data": "item"},
            {"data": "startup"},
            {"data": "host"},
            {"data": "exec_frequency"},
            {"data": "alarm_frequency"},
            {"data": "script"}
        ],
        "columnDefs": [
            {"width": "5%", "targets": 0},
            {"width": "10%", "targets": 1},
            {"width": "10%", "targets": 2},
            {"width": "5%", "targets": 3},
            {"width": "10%", "targets": 4},
            {"width": "5%", "targets": 5},
            {"width": "10%", "targets": 6},
            {"width": "45%", "targets": 7},
        ],
        "columnResizable": true,
        "language": {
            "search": "Key Words:"
        },
        "initComplete": function () {
            var current_table = $('#monitor-details-table').DataTable();
            var api = this.api();
            bind_select_in_column(api);
            bind_input_filter_out_of_table(api, current_table);
            // mark done
            i_am_ready();
        }
    });

    let alarm_table = $('#alarm-details-table').DataTable({
        responsive: true,
        "processing": true,
        "serverSide": false,
        ordering: false,
        "ajax": {
            "url": "/alarm_table_data",
            "type": "GET",
            "data": function (d) {
                d.start = d.start || 0;  // 初始记录索引
                d.length = d.length || 10;  // 页面大小
                d.draw = d.draw || 1;  // 绘制计数器
                d.search = d.search || '';  // 搜索值
                d.order = d.order || [{'column': 0, 'dir': 'asc'}];  // 排序
                d.begin_datetime = $('#begin_datetime').val();
                d.end_datetime = $('#end_datetime').val();
            }
        },
        "columns": [
            {"data": "direction"},
            {"data": "monitor_item"},
            {"data": "time"},
            {"data": "receivers"},
            {"data": "send_alarm_result"},
            {"data": "message"}
        ],
        "columnDefs": [
            {"width": "5%", "targets": 0},
            {"width": "10%", "targets": 1},
            {"width": "10%", "targets": 2},
            {"width": "5%", "targets": 3},
            {"width": "5%", "targets": 4},
            {"width": "65%", "targets": 5},
        ],
        "columnResizable": true,
        "language": {
            "search": "Key Words:"
        },
        "initComplete": function () {
            var current_table = $('#alarm-details-table').DataTable();
            var api = this.api();
            bind_select_in_column(api);
            bind_input_filter_out_of_table(api, current_table);
            // mark done
            i_am_ready();
        },
    });

    let heartbeat_table = $('#heartbeat-details-table').DataTable({
        processing: true,
        serverSide: false,
        ordering: false,
        ajax: {
            "url": "/heartbeat_table_data",
            "type": "GET",
            "data": function (d) {
                d.start = d.start || 0;  // 初始记录索引
                d.length = d.length || 10;  // 页面大小
                d.draw = d.draw || 1;  // 绘制计数器
                d.search = d.search || '';  // 搜索值
                d.order = d.order || [{'column': 0, 'dir': 'asc'}];  // 排序
                d.begin_datetime = $('#begin_datetime').val();
                d.end_datetime = $('#end_datetime').val();
            }
        },
        "columns": [
            {"data": "direction"},
            {"data": "monitor_item"},
            {"data": "time"},
            {"data": "user"},
            {"data": "host"},
            {"data": "script"}
        ],
        "columnDefs": [
            {"width": "5%", "targets": 0},
            {"width": "10%", "targets": 1},
            {"width": "10%", "targets": 2},
            {"width": "5%", "targets": 3},
            {"width": "5%", "targets": 4},
            {"width": "65%", "targets": 5},
        ],
        "columnResizable": true,
        responsive: true,
        "language": {
            "search": "Key Words:"
        },
        "initComplete": function () {
            let current_table = $('#heartbeat-details-table').DataTable();
            let api = this.api();
            bind_select_in_column(api);
            bind_input_filter_out_of_table(api, current_table);
            $("#total-heartbeat-count-p").text("Total Heartbeat: " + api.column(0).data().length)

            // get and format table data
            let heartbeat_table_data = current_table.rows().data();
            let heartbeat_table_records = [];
            heartbeat_table_data.each(function (item) {
                heartbeat_table_records.push(item);
            });
            let chart_data = get_heartbeat_trend_data_from_table(heartbeat_table_records)
            init_heartbeat_trend_chart(chart_data.categories, chart_data.series_data);
            // mark done
            i_am_ready();
        },
    });

    let log_table = $('#log-details-table').DataTable({
        "processing": true,
        "serverSide": false,
        ordering: false,
        "ajax": {
            "url": "/log_table_data",
            "type": "GET",
            "data": function (d) {
                d.start = d.start || 0;  // 初始记录索引
                d.length = d.length || 10;  // 页面大小
                d.draw = d.draw || 1;  // 绘制计数器
                d.search = d.search || '';  // 搜索值
                d.order = d.order || [{'column': 0, 'dir': 'asc'}];  // 排序
                d.begin_datetime = $('#begin_datetime').val();
                d.end_datetime = $('#end_datetime').val();
            }
        },
        "columns": [
            {"data": "direction"},
            {"data": "monitor_item"},
            {"data": "time"},
            {"data": "message_level"},
            {"data": "message"}
        ],
        "columnDefs": [
            {"width": "5%", "targets": 0},
            {"width": "10%", "targets": 1},
            {"width": "10%", "targets": 2},
            {"width": "5%", "targets": 3},
            {"width": "70%", "targets": 4},
        ],
        "columnResizable": true,
        responsive: true,
        "language": {
            "search": "Key Words:"
        },
        "initComplete": function () {
            let current_table = $('#log-details-table').DataTable();
            let api = this.api();
            bind_select_in_column(api);
            bind_input_filter_out_of_table(api, current_table);

            // get and format table data
            let log_table_data = current_table.rows().data();
            let log_table_records = [];
            log_table_data.each(function (item) {
                log_table_records.push(item);
            });
            let chart_data = get_logs_trend_data_from_table(log_table_records);
            // init charts with formatted table data
            init_log_trend_chart(chart_data.categories, chart_data.series_data);

            // mark done
            i_am_ready();
        },
    });
    return [monitor_table, alarm_table, heartbeat_table, log_table];
}

function init_alarm_chart(categories, series_data) {
    Highcharts.chart('alarm-chart', {
        chart: {
            type: 'line',
            events: {
                load: function () {
                    // mark done
                    i_am_ready();
                }
            }
        },
        title: {
            text: 'Alarm Trend',
            align: 'left'
        },
        subtitle: {
            text: 'by direction',
            align: 'left'
        },
        xAxis: {
            categories: categories
        },
        yAxis: {
            title: {
                text: 'Count of Alarms'
            }
        },
        series: series_data,
        credits: {
            enabled: false
        },
    });
}

function init_monitor_chart(categories, series_data) {
    Highcharts.chart('monitor-chart', {
        chart: {
            type: 'bar',
            events: {
                load: function () {
                    // mark done
                    i_am_ready();
                }
            }
        },
        title: {
            text: 'Top 10 Alarms',
            align: 'left'
        },
        subtitle: {
            text: 'by monitor item',
            align: 'left'
        },
        xAxis: {
            categories: categories,
        },
        yAxis: {
            min: 0,
            title: {
                text: 'Alarm count',
                align: 'high'
            },
            labels: {
                overflow: 'justify'
            },
            gridLineWidth: 0
        },
        plotOptions: {
            bar: {
                borderRadius: '50%',
                dataLabels: {
                    enabled: true
                },
                groupPadding: 0.1
            }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            x: -40,
            y: 80,
            floating: true,
            borderWidth: 1,
            backgroundColor:
                Highcharts.defaultOptions.legend.backgroundColor || '#FFFFFF',
            shadow: true
        },
        credits: {
            enabled: false
        },
        series: series_data
    });
}

function init_heartbeat_trend_chart(categories, series_data) {
    Highcharts.chart('heartbeat-chart', {
        chart: {
            type: 'line',
            events: {
                load: function () {
                    // mark done
                    i_am_ready();
                }
            }
        },
        title: {
            text: 'Heartbeat Trend',
            align: 'left'
        },
        subtitle: {
            text: 'by direction',
            align: 'left'
        },
        yAxis: {
            title: {
                text: 'Number of heartbeat log'
            }
        },
        xAxis: {
            categories: categories
        },
        series: series_data,
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle'
        }, responsive: {
            rules: [{
                condition: {
                    maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        layout: 'horizontal',
                        align: 'center',
                        verticalAlign: 'bottom'
                    }
                }
            }]
        }
    });
}

function init_log_trend_chart(categories, series_data) {
    Highcharts.chart('error-log-chart', {
        chart: {
            type: 'column',
            events: {
                load: function () {
                    console.log("log trend chart loaded!")
                    // mark done
                    i_am_ready();
                }
            }
        },
        title: {
            text: 'Logs Trend',
            align: 'left'
        },
        subtitle: {
            text: 'by direction & log level',
            align: 'left'
        },
        xAxis: {
            categories: categories
        },
        yAxis: {
            allowDecimals: false,
            min: 0,
            title: {
                text: 'Count logs'
            }
        },
        tooltip: {
            format: '<b>{key}</b><br/>{series.name}: {y}<br/>' +
                'Total: {point.stackTotal}'
        },
        plotOptions: {
            column: {
                stacking: 'normal'
            }
        },
        credits: {
            enabled: false
        },
        series: series_data
    });
}

function bind_input_filter_out_of_table(api, table) {
    $(".mdc-text-field__input").on('change', function () {
        on_input_filter_change(api);
    })
}

function bind_select_in_column(api) {
    api.columns().every(function () {
        var column = this;
        var select = $('<select class="form-control form-control-sm"><option value="">All</option></select>')
            .appendTo($(column.header()))
            .on('change', function () {
                on_column_change(api, column, $(this));
            });

        // 添加列中的选项
        column.data().unique().sort().each(function (d) {
            select.append('<option value="' + d.replace(/"/g, '&quot;') + '">' + d + '</option>');
        });

        select.select2({
            placeholder: "Select option",
            allowClear: true
        });
    });
}

function on_column_change(api, column, select) {
    var val = select.val();
    column.search(val ? val : '', false, false).draw();

    var currentColumnIndex = column.index();

    let only_one_filter_index = 0;
    let filter_num = 0;
    api.columns().every(function (i) {
        var otherSelect = $(this.header()).find('select');
        var currentFilterValue = otherSelect.val(); // 获取当前选择的值
        if (currentFilterValue.length != 0) {
            filter_num = filter_num + 1;
            only_one_filter_index = i;
        }
    })
    if ($(".mdc-text-field__input").val().length !== 0) {
        filter_num = filter_num + 1;
        only_one_filter_index = -1;
    }

    api.columns().every(function (i) {
        if (i !== currentColumnIndex) {
            var otherSelect = $(this.header()).find('select');
            var currentFilterValue = otherSelect.val(); // 获取当前选择的值
            otherSelect.empty().append('<option value="">All</option>');
            if (filter_num === 1 && only_one_filter_index === i) {
                api.column(i).data().unique().sort().each(function (d) {
                    otherSelect.append('<option value="' + d.replace(/"/g, '&quot;') + '">' + d + '</option>');
                });
            } else {
                api.column(i, {search: 'applied'}).data().unique().sort().each(function (d) {
                    otherSelect.append('<option value="' + d.replace(/"/g, '&quot;') + '">' + d + '</option>');
                });
            }
            otherSelect.val(currentFilterValue); // 重新设置之前选择的值
        }
    });
}

function on_input_filter_change(api) {
    api.columns().every(function (i) {
        var otherSelect = $(this.header()).find('select');
        var currentFilterValue = otherSelect.val(); // 获取当前选择的值
        if (api.column(i, {search: 'applied'}).data().unique().length === 0) {
            otherSelect.val(currentFilterValue);
            return;
        }
        otherSelect.empty().append('<option value="">All</option>');
        api.column(i, {search: 'applied'}).data().unique().sort().each(function (d) {
            otherSelect.append('<option value="' + d.replace(/"/g, '&quot;') + '">' + d + '</option>');
        });
        otherSelect.val(currentFilterValue); // 重新设置之前选择的值
    });
}

function toggleTabs(className, element) {
    $('.nav-link').removeClass('active'); // 先移除所有元素的 active 类
    $('.' + className).addClass('active'); // 添加 active 类到被点击的元素

    var target = element.getAttribute("roll_to");
    var collapseContent = document.querySelectorAll(".collapse");

    collapseContent.forEach(function (item) {
        if (item.id !== target.substring(1)) {
            item.classList.remove("show");
        } else {
            item.classList.add("show");
        }
    });

    $('#log-details-table').DataTable().columns.adjust().draw();
    $('#heartbeat-details-table').DataTable().columns.adjust().draw();
    $('#alarm-details-table').DataTable().columns.adjust().draw();

    if (element.tagName === 'A') {
        return;
    }
    window.location.href = target;
}

function get_logs_trend_data_from_table(log_table_data) {
    // order by time
    log_table_data.sort(function (a, b) {
        return new Date(a['time']) - new Date(b['time']);
    });
    let log_trend_categories = [];
    let log_trend_series_data = [];
    // init chart when no data None
    if (Array.isArray(log_table_data)) {
        if (log_table_data.length === 0) {
            return {
                categories: log_trend_categories,
                series_data: log_trend_series_data
            };
        }
    }
    // init chart when >= 1 record [{}]
    // init categories
    log_trend_categories = generateDates(
        log_table_data[0]['time'].substring(0, 10),
        log_table_data[log_table_data.length - 1]['time'].substring(0, 10));


    // init series data with default value
    log_table_data.forEach(function (item) {
        if (!log_trend_series_data.some(function (element) {
            return element['name'] === item['direction'] + '-' + item['message_level']
                && element['stack'] === item['direction'];
        })) {
            log_trend_series_data.push({
                name: item['direction'] + '-' + item['message_level'],
                data: new Array(log_trend_categories.length).fill(0),
                stack: item['direction']
            });
        }
    });

    // update series data with calculated value
    log_table_data.forEach(function (item, index) {
        let series_index = log_trend_series_data.findIndex(function (element) {
            return element['name'] === item['direction'] + '-' + item['message_level']
                && element['stack'] === item['direction'];
        })
        if (series_index !== -1) {
            var dataIndex = log_trend_categories.indexOf(item['time'].substring(0, 10));
            log_trend_series_data[series_index].data[dataIndex] += 1;
        }
    });

    return {
        categories: log_trend_categories,
        series_data: log_trend_series_data
    };
}

function get_heartbeat_trend_data_from_table(heartbeat_table_data) {
    // order by time
    heartbeat_table_data.sort(function (a, b) {
        return new Date(a['time']) - new Date(b['time']);
    });
    let heartbeat_trend_categories = [];
    let heartbeat_trend_series_data = [];
    // init chart when no data None
    if (Array.isArray(heartbeat_table_data)) {
        if (heartbeat_table_data.length === 0) {
            return {
                categories: heartbeat_trend_categories,
                series_data: heartbeat_trend_series_data
            };
        }
    }
    // init chart when >= 1 record [{}]
    // init categories
    heartbeat_trend_categories = generateDates(
        heartbeat_table_data[0]['time'].substring(0, 10),
        heartbeat_table_data[heartbeat_table_data.length - 1]['time'].substring(0, 10));

    // init series data with default value
    heartbeat_table_data.forEach(function (item) {
        if (!heartbeat_trend_series_data.some(function (element) {
            return element['name'] === item['direction'];
        })) {
            heartbeat_trend_series_data.push({
                name: item['direction'],
                data: new Array(heartbeat_trend_categories.length).fill(0)
            });
        }
    });

    // update series data with calculated value
    heartbeat_table_data.forEach(function (item) {
        let series_index = heartbeat_trend_series_data.findIndex(function (element) {
            return element['name'] === item['direction'];
        })
        if (series_index !== -1) {
            var dataIndex = heartbeat_trend_categories.indexOf(item['time'].substring(0, 10));
            heartbeat_trend_series_data[series_index].data[dataIndex] += 1;
        }
    });

    return {
        categories: heartbeat_trend_categories,
        series_data: heartbeat_trend_series_data
    };
}

function generateDates(startDateStr, endDateStr) {
    var startDate = new Date(startDateStr);
    var endDate = new Date(endDateStr);
    var dates = [];

    // 将开始日期推送到数组中
    dates.push(startDateStr);

    // 循环生成开始日期和结束日期之间的日期，并推送到数组中
    while (startDate < endDate) {
        startDate.setDate(startDate.getDate() + 1);
        dates.push(startDate.toISOString().slice(0, 10));
    }

    return dates;
}

function i_am_ready() {
    // 获取数据
    let progress = localStorage.getItem('progress');
    if (progress === null) {
        localStorage.setItem('progress', 1);
    } else {
        localStorage.setItem('progress', parseInt(progress) + 1);
    }
}
