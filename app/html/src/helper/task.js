function getStatusColor(status) {
    let progressColor = 'blue';
    if (status == 'done') {
        progressColor = 'green'
    } else if (status == 'ready') {
        progressColor = 'grey'
    } else if (status == 'error') {
        progressColor = 'red'
    } else if (status == 'stopped') {
        progressColor = 'deep-orange'
    }
    progressColor += ' darken-4'
    return progressColor
}


function getItemsTotalStatus(items) {
    let status = 'done';

    for (let v of items) {
        if (v.status == 'stopped') {
            status = 'stopped'
            break
        } else if (v.status == 'running') {
            status = 'running'
            break
        } else if (v.status == 'error') {
            status = 'error'
            break
        } else if (v.status == 'ready') {
            status = 'ready'
        }
    }
    return status;
}

export {
    getStatusColor,
    getItemsTotalStatus,
};