// app/page.tsx

import PasswordForm from './components/PasswordForm';

const PasswordHomePage: React.FC = () => {
  return (
    // Centering layout using flexbox
    <main className="flex min-h-screen items-center justify-center bg-white text-black">
      <PasswordForm />
    </main>
  );
}

export default PasswordHomePage;