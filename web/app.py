from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
from service.monitor_service import MonitorService
from tools.decorator_helper import print_execution_time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bootstrap = Bootstrap(app)


@app.route('/top_alarms_per_monitor_item', methods=['GET'])
@print_execution_time
def get_top_alarms_per_monitor_item():
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    top_alarms_data = monitor_service.get_top_alarms_per_monitor_item(begin_date, end_date)
    categories = [inner_list[0] for inner_list in top_alarms_data]
    series_datas = []

    for alarm_data in top_alarms_data:
        series_datas.append({
            'name': alarm_data[0],
            'data': [alarm_data[1]]
        })

    data = {
        'categories': categories,
        'series': series_datas,
    }

    return jsonify(data)


@app.route('/monitor_chart_data', methods=['GET'])
@print_execution_time
def get_monitor_chart_data():
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    categories, series_data = monitor_service.get_monitor_chart_data(begin_date, end_date)
    data = {
        'categories': categories,
        'series': series_data,
    }

    return jsonify(data)


@app.route('/alarm_chart_data', methods=['GET'])
@print_execution_time
def get_alarm_chart_data():
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    categories, series_data = monitor_service.get_alarm_chart_data(begin_date, end_date)
    data = {
        'categories': categories,
        'series': series_data,
    }

    return jsonify(data)


@app.route('/monitor_table_data', methods=['GET'])
@print_execution_time
def get_monitor_table_data():
    draw = request.args.get('draw')
    search_value = request.args.get('search[value]')
    order_column_index = int(request.args.get('order[0][column]'))
    order_direction = request.args.get('order[0][dir]')
    monitor_service = MonitorService()
    data = monitor_service.get_monitor_table_data()
    # 进行搜索过滤
    filtered_data = []

    if search_value:
        for item in data:
            if search_value.lower() in str(item.values()).lower():
                filtered_data.append(item)
    else:
        filtered_data = data

    # 进行排序
    if order_direction == 'asc':
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index])
    else:
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index], reverse=True)

    # 获取当前页的数据
    paginated_data = sorted_data

    return jsonify({
        "draw": draw,
        "recordsTotal": len(data),
        "recordsFiltered": len(filtered_data),
        "data": paginated_data
    })


@app.route('/heartbeat_table_data', methods=['GET'])
@print_execution_time
def get_heartbeat_table_data():
    draw = request.args.get('draw')
    search_value = request.args.get('search[value]')
    order_column_index = int(request.args.get('order[0][column]'))
    order_direction = request.args.get('order[0][dir]')
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    data = monitor_service.get_all_heartbeat_table_data(begin_date, end_date)
    # 进行搜索过滤
    filtered_data = []

    if search_value:
        for item in data:
            if search_value.lower() in str(item.values()).lower():
                filtered_data.append(item)
    else:
        filtered_data = data

    # 进行排序
    if order_direction == 'asc':
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index])
    else:
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index], reverse=True)

    # 获取当前页的数据
    paginated_data = sorted_data

    return jsonify({
        "draw": draw,
        "recordsTotal": len(data),
        "recordsFiltered": len(filtered_data),
        "data": paginated_data
    })


@app.route('/alarm_table_data', methods=['GET'])
@print_execution_time
def get_alarm_table_data():
    draw = request.args.get('draw')
    search_value = request.args.get('search[value]')
    order_column_index = int(request.args.get('order[0][column]'))
    order_direction = request.args.get('order[0][dir]')
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    data = monitor_service.get_all_alarm_table_data(begin_date, end_date)
    # 进行搜索过滤
    filtered_data = []

    if search_value:
        for item in data:
            if search_value.lower() in str(item.values()).lower():
                filtered_data.append(item)
    else:
        filtered_data = data

    # 进行排序
    if order_direction == 'asc':
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index])
    else:
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index], reverse=True)

    # 获取当前页的数据
    paginated_data = sorted_data

    return jsonify({
        "draw": draw,
        "recordsTotal": len(data),
        "recordsFiltered": len(filtered_data),
        "data": paginated_data
    })


@app.route('/log_table_data', methods=['GET'])
@print_execution_time
def get_log_table_data():
    draw = request.args.get('draw')
    search_value = request.args.get('search[value]')
    order_column_index = int(request.args.get('order[0][column]'))
    order_direction = request.args.get('order[0][dir]')
    begin_date = request.args.get('begin_datetime')
    end_date = request.args.get('end_datetime')
    monitor_service = MonitorService()
    data = monitor_service.get_all_log_table_data(begin_date, end_date)
    # 进行搜索过滤
    filtered_data = []

    if search_value:
        for item in data:
            if search_value.lower() in str(item.values()).lower():
                filtered_data.append(item)
    else:
        filtered_data = data

    # 进行排序
    if order_direction == 'asc':
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index])
    else:
        sorted_data = sorted(filtered_data, key=lambda x: list(x.values())[order_column_index], reverse=True)

    # 获取当前页的数据
    paginated_data = sorted_data

    return jsonify({
        "draw": draw,
        "recordsTotal": len(data),
        "recordsFiltered": len(filtered_data),
        "data": paginated_data
    })


@app.route('/', methods=['GET'])
@print_execution_time
def monitor_overview():
    current_time = datetime.now()
    # 减去一天
    one_day_delta = timedelta(days=7)
    previous_day_time = current_time - one_day_delta
    begin_datetime = request.args.get('begin_datetime')
    end_datetime = request.args.get('end_datetime')

    if begin_datetime is None or len(begin_datetime) == 0:
        begin_datetime = previous_day_time.strftime("%Y-%m-%d %H:%M:%S")

    if end_datetime is None or len(end_datetime) == 0:
        end_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")

    monitor_service = MonitorService()
    alarm_count = monitor_service.get_alarm_count(begin_datetime, end_datetime)
    monitor_count = monitor_service.get_monitor_count()
    error_log_count = monitor_service.get_error_log_count(begin_datetime, end_datetime)

    return render_template('layouts/overview.html',
                           alarm_count=alarm_count,
                           monitor_count=monitor_count,
                           error_log_count=error_log_count,
                           begin_date_time=begin_datetime,
                           end_date_time=end_datetime)


if __name__ == '__main__':
    app.run(port=80)
