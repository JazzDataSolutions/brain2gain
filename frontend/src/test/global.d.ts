declare namespace NodeJS {
  interface Global {
    mockNavigate: jest.Mock
  }
}

declare global {
  var mockNavigate: jest.Mock
}
