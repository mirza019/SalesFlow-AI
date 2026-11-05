import { Link, Outlet } from 'react-router-dom'
export default function MainLayout(){return <><header><strong>SalesFlow AI</strong><nav><Link to="/">Dashboard</Link></nav></header><main><Outlet/></main></>}

