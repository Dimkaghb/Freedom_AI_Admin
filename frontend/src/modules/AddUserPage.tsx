import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AddUser } from './addUser';
import apiClient from '@/lib/axios';
import { useAuth } from '@/shared/stores/authstore';

interface User {
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  tempPassword: string;
}

export const AddUserPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { user: currentUser, isLoading: authLoading } = useAuth();

  // Debug logging
  console.log('AddUserPage - Current User:', currentUser);
  console.log('AddUserPage - User Role:', currentUser?.role);

  const handleAddUser = async (user: User) => {
    setIsLoading(true);

    try {
      // Call backend API to create user
      const response = await apiClient.post('/users/create', {
        email: user.email,
        role: user.role,
        full_name: `${user.firstName} ${user.lastName}`,
        // Backend generates password automatically, so we don't send it
      });

      console.log('User created successfully:', response.data);

      // Show success message (you can add a toast notification here)
      alert(`User created successfully!\nEmail: ${user.email}\nTemporary Password: ${response.data.temporary_password}`);

      // Navigate back to dashboard or user management page
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error creating user:', error);

      // Show error message
      const errorMessage = error.response?.data?.detail || 'Failed to create user';
      alert(`Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
          <p className="mt-2 text-sm text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Check if current user exists
  if (!currentUser) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Не авторизован</h1>
          <p className="text-gray-600 mt-2">Пожалуйста, войдите в систему для доступа к этой странице.</p>
        </div>
      </div>
    );
  }

  // Check if current user is admin (temporarily disabled)
  // TODO: Re-enable admin check after fixing user roles in database
  // if (currentUser.role !== 'admin') {
  //   return (
  //     <div className="flex items-center justify-center min-h-screen">
  //       <div className="text-center">
  //         <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
  //         <p className="text-gray-600 mt-2">
  //           You don't have permission to access this page.
  //         </p>
  //         <p className="text-sm text-gray-500 mt-2">
  //           Current role: {currentUser.role || 'unknown'}
  //         </p>
  //         <p className="text-sm text-gray-500">
  //           Required role: admin
  //         </p>
  //       </div>
  //     </div>
  //   );
  // }

  return <AddUser onAddUser={handleAddUser} isLoading={isLoading} />;
};
