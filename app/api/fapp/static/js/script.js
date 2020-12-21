STATUS_MAPPING = {
    'queuing': '#999',
    'running': '#428bca',
    //    '3': 'orange',
    'unknown': '#8a6d3b',
    'error': '#a94442',
    'done': '#3c763d',
}

PROGRESS_BAR_COLOR_LIST = [
    'bg-success', 'bg-info', 'bg-warning', 'bg-danger', '',
]


$(function() {



    // function downloadInfoLoader(data) {

    //     data.speed / 1024

    // }

    // function ffmpegInfoLoader(data) {

    // }

    // function defaultInfoLoader(data) {

    // }
    // window.InfoLoader = {
    //     'download': downloadInfoLoader,
    //     'ffmpeg': ffmpegInfoLoader,
    //     '': defaultInfoLoader,

    // }
    // window.requesterInfo = {}

    //    function getRequesterInfo(){
    //        $.ajax({
    //            type:'GET',
    //            url:'./requesterInfo',
    //            cache: false,
    //            dataType:'json',
    //            success: function(data){
    //                window.requesterInfo = data;
    //
    //                clearInterval(getTaskListInfo);
    //                setInterval(getTaskListInfo, 1000);
    //            },
    //            error: function(){
    //                setTimeout(getRequesterInfo, 2000);
    //                console.log("请求失败");
    //            }
    //        })
    //    }

    function getConfigInfo() {
        $.ajax({
            type: 'GET',
            url: '/configInfo',
            cache: false,
            dataType: 'json',
            success: function(data) {
                $('#storage_dir').val(data.basic['storage_dir']);
                $('#tempdir').val(data.basic['tempdir']);
                console.log(data);
            },
            error: function() {
                setTimeout(getConfigInfo, 2000);

            }
        })
    }

    function getTaskListInfo() {
        $.ajax({
            type: 'GET',
            url: '/lstTasks',
            cache: false,
            dataType: 'json',
            success: function(data) {
                $.each(data, function(k, v) {
                    updateTask(k, v)
                })
            },
            error: function() {
                console.log("请求失败");
            }
        })

    }

    // function updateTask() {

    // }

    function updateTask(key, data) {
        var taskNode = $('#Task-' + key);
        taskNode.length == 0 && (addNewTask({ 'key': key, 'url': data['url'] }), taskNode = $('#Task-' + key));
        // 更新主标题
        data.title && taskNode.find('.task-title').text(data['title']);

        // 更新状态标志条
        data.status && taskNode.find('.task-status').css('background-color', STATUS_MAPPING[String(data['status'])]);

        // 更新进度条
        taskNode.find('.task-percent').text(data['percent'].toFixed(2) + '%');
        taskNode.find('.task-body').text(data.url);

        // var requestPercent = {};
        // $.each(data.flows, function(i, flow) {
        //     $.each(flow.branches, function(ii, branch) {
        //         $.each(branch.all, function(iii, node) {
        //             var name = node.name;
        //             requestPercent[name] || (requestPercent[name] = [0, 0]);
        //             requestPercent[name][0] += node.percent;
        //             requestPercent[name][1] += 1;
        //         });
        //     });
        // });
        var progressNode = taskNode.find('.task-progress');
        $.each(data['requesterRatio'], function(k, v) {
            // var percent = v['percent'];
            var requestNode = progressNode.find('[requester="' + v['name'] + '"]');
            var nodeIndex = requestNode.index();
            nodeIndex == -1 && (nodeIndex = progressNode.children().length);

            if (requestNode.length == 0) {
                progressNode.append($('<div class="progress-bar ' + PROGRESS_BAR_COLOR_LIST[nodeIndex % 5] + '" requester="' + v['name'] + '" style="width: 0%;">' + v['name'] + '</div>'))
                requestNode = progressNode.find('[requester="' + v['name'] + '"]');
            }
            requestNode.css('width', v['percent'] + '%');
        });
        // 通过请求器的权重得到占比
        // var totalWeight = 0;
        // for (var k in requestPercent) {
        //     totalWeight += requesterInfo[k].weight;
        // }
        // $.each(requestPercent, function(k, v) {
        //     var percent = (v[0] / v[1]).toFixed(2);
        //     var requestNode = progressNode.find('[requester="' + k + '"]');
        //     var nodeIndex = requestNode.index();
        //     nodeIndex == -1 && (nodeIndex = progressNode.children().length);

        //     requestNode.length == 0 &&
        //         progressNode.append($('<div class="progress-bar ' + PROGRESS_BAR_COLOR_LIST[nodeIndex % 5] + '" requester="' + k + '" style="width: 0%;">' + k + '</div>')) &&
        //         (requestNode = progressNode.find('[requester="' + k + '"]'));
        //     requestNode.css('width', (percent * (requesterInfo[k].weight / totalWeight)).toFixed(2) + '%');
        // });

        // 更新最新日志信息
        // taskNode.find('.task-tip').attr('title', data.latest);


    }




    function addNewTask(result) {
        var taskList = $('.container .tasks');
        var taskNode = taskList.find('#Task-' + result.key);
        taskNode.length == 0 && (taskNode = $(
            '<li class="task"  id="Task-' + result.key + '">' +
            '<div class="task-status"></div>' +
            '<div class="task-thumbnail">' +
            '<a href="#">' +
            '<img class="img-rounded profile-thumbnail" src="">' +
            '</a>' +
            '</div>' +
            '<div class="task-content">' +
            '<div class="task-tip fa fa-lightbulb-o" data-toggle="tooltip" title=""></div>' +
            '<div class="task-title">' + result.key + '</div>' +
            '<div class="task-percent">0%</div>' +
            '<div class="task-body">' + result.url + '</div>' +
            '<div class="task-footer">' +
            '<div class="progress task-progress">' +
            '</div>' +
            '</div>' +
            '</li>'), taskList.append(taskNode));
    }



    $('#submitTaskForm').submit(function(e) { return false; })
    $('#submit').click(function() {
        var data = $("#submitTaskForm").serialize();
        $.ajax({
            type: 'POST',
            url: '/new',
            cache: false,
            data: data,
            dataType: 'json',
            success: function(data) {
                $.each(data, function(k, v) {
                    v.code == 0 && addNewTask(v);
                });
                $('#urls').val('');
            },
            error: function() {
                alert("请求失败")
            }
        })
    });
    $('a[href="#settings-content"]').on('shown.bs.tab', function(e) {
        getConfigInfo();
    });

    //    getRequesterInfo();
    setInterval(getTaskListInfo, 1000);

})