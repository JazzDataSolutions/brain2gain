// Dashboard.tsx
export interface DashboardProps {
  userName: string;
  notifications: number;
}

const Dashboard: React.FC<DashboardProps> = ({ userName, notifications }) => {
  return (
    <div>
      <h1>Bienvenido, {userName}</h1>
      <p>Tienes {notifications} notificaciones</p>
    </div>
  );
};

export default Dashboard;

