import pygame
import random
import math

class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 3
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 200 * dt  # gravity
        self.lifetime -= dt
        
    def is_alive(self):
        return self.lifetime > 0
        
    def draw(self, screen):
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


class EffectManager:
    def __init__(self):
        self.particles = []
        
    def add_particle_burst(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 50
            lifetime = random.uniform(0.3, 0.6)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime))
        
    def update(self, dt):
        # Update particles
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update(dt)
            
    def draw(self, screen, font):
        # Draw particles
        for particle in self.particles:
            particle.draw(screen)