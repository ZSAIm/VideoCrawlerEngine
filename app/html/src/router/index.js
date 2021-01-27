import TaskPage from '@/views/pages/main/TaskPage'
import Settings from '@/views/pages/main/Settings'
import TaskNav from '@/views/pages/nav/TaskNav'

const routes = [{
    path: '/',
    name: 'index',
    components: {
        main: TaskPage,
        nav: TaskNav,
    }
}, {
    path: '/settings',
    name: 'Settings',
    components: {
        main: Settings,
        nav: TaskNav,
    }
}];

export default routes;