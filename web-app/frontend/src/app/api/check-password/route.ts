// app/api/check-password/route.js

import { NextResponse } from 'next/server';

// Get the password from environment variables
const CORRECT_PASSWORD = process.env.PASSWORD;

/**
 * Handles POST requests to check the password.
 */
export async function POST(request: Request) {
  try {
    const { password } = await request.json();

    if (!password) {
      return NextResponse.json({ success: false, message: 'Password is required' }, { status: 400 });
    }

    // Simple comparison for development
    if (password === CORRECT_PASSWORD) {
      // In a real app, you might set a secure, expiring cookie here
      return NextResponse.json({ success: true, message: 'Access granted' }, { status: 200 });
    } else {
      return NextResponse.json({ success: false, message: 'Incorrect password' }, { status: 401 });
    }
  } catch (error) {
    console.error('Password check error:', error);
    return NextResponse.json({ success: false, message: 'Internal Server Error' }, { status: 500 });
  }
}