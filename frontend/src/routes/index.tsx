import { createBrowserRouter } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import Dashboard from '../pages/Dashboard'
import Login from '../pages/Login'
export const router = createBrowserRouter([{path:'/login',element:<Login/>},{path:'/',element:<MainLayout/>,children:[{index:true,element:<Dashboard/>}]}])

