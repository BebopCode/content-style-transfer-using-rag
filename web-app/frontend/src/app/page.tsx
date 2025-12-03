// app/page.tsx

import PasswordForm from './components/PasswordForm';

const PasswordHomePage: React.FC = () => {
  return (
    // Centering layout using flexbox
    <div className="flex flex-row min-h-screen  mt-40 justify-center bg-white text-black">
      <div className='text-5xl'>
        Content Style Transfer using RAG
      </div>

    </div>
  );
}

export default PasswordHomePage;