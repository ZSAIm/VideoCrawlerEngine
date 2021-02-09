import TaskPage from '@/views/pages/main/TaskPage'
import SettingsPage from '@/views/pages/main/SettingsPage'
import InformationPage from '@/views/pages/main/InformationPage'
import TaskNav from '@/views/pages/nav/TaskNav'
import SettingsNav from '@/views/pages/nav/SettingsNav'
import InformationNav from '@/views/pages/nav/InformationNav'

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
        main: SettingsPage,
        nav: SettingsNav,
    },
}, {
    path: '/info',
    name: 'info',
    components: {
        main: InformationPage,
        nav: InformationNav,
    },

}, ];

export default routes;