
from helper.ctxtools.mgr import ObjectMappingContext, ContextManager

progress_mapping_context = ObjectMappingContext(
    attrs='percent speed timeleft statu',
    meths="""
    upload start close task_done 
    getdata iterdata error success 
    info warning report add_stopper stop
    """
)

request_mapping_context = ObjectMappingContext(
    attrs='NAME',
    meths='end_request error_handler ',
)
self_request = ContextManager('__request__')
config_context = ContextManager('config', {})
