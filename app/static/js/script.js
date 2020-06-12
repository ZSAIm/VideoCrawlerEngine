
// 任务提交
$(function(){
    $('#newTaskForm').submit(function(e){return false;})
    $('#submit').click(function(){
        var data = $("#newTaskForm").serialize();
        $.ajax({
            type:'POST',
            url:'./new',
            cache: false,
            data:data,
            dataType:'json',
            success:function(data){
                alert('success');
            },
            error:function(){
                alert("请求失败")
            }
       })
    })


})



