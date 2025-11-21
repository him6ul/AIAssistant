//
//  APIClient.swift
//  AI Personal Assistant
//
//  API client for communicating with the FastAPI backend
//

import Foundation

struct APIClient {
    private let baseURL = "http://localhost:8000"
    
    // MARK: - Chat
    
    struct ChatRequest: Codable {
        let message: String
        let systemPrompt: String?
        
        enum CodingKeys: String, CodingKey {
            case message
            case systemPrompt = "system_prompt"
        }
    }
    
    struct ChatResponse: Codable {
        let response: String
        let mode: String
        let model: String
    }
    
    func sendChat(message: String, completion: @escaping (ChatResponse?) -> Void) {
        let request = ChatRequest(message: message, systemPrompt: nil)
        
        guard let url = URL(string: "\(baseURL)/chat") else {
            completion(nil)
            return
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            urlRequest.httpBody = try JSONEncoder().encode(request)
        } catch {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
                completion(chatResponse)
            } catch {
                print("Decode error: \(error)")
                completion(nil)
            }
        }.resume()
    }
    
    // MARK: - Tasks
    
    func getTasks(completion: @escaping ([Task]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let tasks = try JSONDecoder().decode([Task].self, from: data)
                completion(tasks)
            } catch {
                print("Decode error: \(error)")
                completion(nil)
            }
        }.resume()
    }
    
    func getTasksToday(completion: @escaping ([Task]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks/today") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let tasks = try JSONDecoder().decode([Task].self, from: data)
                completion(tasks)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    func getTasksOverdue(completion: @escaping ([Task]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks/overdue") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let tasks = try JSONDecoder().decode([Task].self, from: data)
                completion(tasks)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    func getTasksWaitingOn(completion: @escaping ([Task]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks/waiting-on") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let tasks = try JSONDecoder().decode([Task].self, from: data)
                completion(tasks)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    func getTasksFollowUps(completion: @escaping ([Task]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks/follow-ups") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let tasks = try JSONDecoder().decode([Task].self, from: data)
                completion(tasks)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    // MARK: - Ingestion
    
    struct ScanResponse: Codable {
        let emailsProcessed: Int?
        let pagesProcessed: Int?
        let status: String
        
        enum CodingKeys: String, CodingKey {
            case emailsProcessed = "emails_processed"
            case pagesProcessed = "pages_processed"
            case status
        }
    }
    
    func scanEmails(completion: @escaping (ScanResponse?) -> Void) {
        guard let url = URL(string: "\(baseURL)/ingestion/email/scan") else {
            completion(nil)
            return
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let result = try JSONDecoder().decode(ScanResponse.self, from: data)
                completion(result)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    func scanOneNote(completion: @escaping (ScanResponse?) -> Void) {
        guard let url = URL(string: "\(baseURL)/ingestion/onenote/scan") else {
            completion(nil)
            return
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let result = try JSONDecoder().decode(ScanResponse.self, from: data)
                completion(result)
            } catch {
                completion(nil)
            }
        }.resume()
    }
    
    // MARK: - Status
    
    struct StatusResponse: Codable {
        let network: String
        let llmMode: String
        let status: String
        
        enum CodingKeys: String, CodingKey {
            case network
            case llmMode = "llm_mode"
            case status
        }
    }
    
    func getStatus(completion: @escaping (StatusResponse?) -> Void) {
        guard let url = URL(string: "\(baseURL)/status") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            do {
                let status = try JSONDecoder().decode(StatusResponse.self, from: data)
                completion(status)
            } catch {
                completion(nil)
            }
        }.resume()
    }
}

